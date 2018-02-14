#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
from fnmatch import fnmatch
from scheduler import Launcher, check_file_repeat
from sys import platform
from subprocess import call
from shutil import rmtree, copyfile
import numpy as np
import SimpleITK as sitk
from scipy.spatial.distance import correlation, dice
from pickle import dump

parser = argparse.ArgumentParser()
parser.add_argument("--in_dir", type=str, nargs=1, required=True)
parser.add_argument("--in_suffix", type=str, nargs=1, required=True)
parser.add_argument("--in2_dir", type=str, nargs=1, help="(optional) if not given, LOO in in_dir is used")
parser.add_argument("--in2_suffix", type=str, nargs=1, help="(optional) if not given, LOO in in_dir is used")
parser.add_argument("--mask_file", type=str, nargs=1, help="(optional) mask of region to compare")
parser.add_argument("--method", type=str, nargs='+', required=True, help='[Dice, [labels_list ...| nothing for all]] | Correlation | [NormalizedCorrelation, tmp_dir]')
parser.add_argument("--out_file", type=str, nargs=1, required=True, help="output file with pairwise similarities")

args = parser.parse_args()
# args = parser.parse_args('--in_dir /Users/gsanroma/DATA/DATABASES/ADNI/atlases/registration_100x100x0x0 --in_suffix _brainXtemplateWarped.nii.gz --method NormalizedCorrelation /Users/gsanroma/DATA/DATABASES/ADNI/atlases/tmp_similarity --out_file /Users/gsanroma/DATA/DATABASES/ADNI/atlases/NormalizedCorrelation.dat'.split())
# args = parser.parse_args('--in_dir /Users/gsanroma/DATA/DATABASES/ADNI/atlases/registration_100x100x0x0 --in_suffix _brainXtemplateWarped.nii.gz --method Correlation --out_file /Users/gsanroma/DATA/DATABASES/ADNI/atlases/Correlation.dat'.split())

os.environ["ANTSPATH"] = "/homedtic/gsanroma/CODE/LIB/ANTs/build/bin"

os.environ["ANTSSCRIPTS"] = "/homedtic/gsanroma/CODE/LIB/ANTs/Scripts"

n_jobs = 0
n_total_jobs = 80
list_of_jobs = []

def resample_image(img, spacing, sz_out = None, sp_out = None):
    """Resample brain MRI image to specified spacing, size_out and spacing out

    img: The MRI image to resample.

    spacing: The spacing of the image we want.

    sz_out: The size of the output image. If it is not specified, we calculate it.

    sp_out: spacing of the final image. If it is not specified, we calculate it.

    Function taken from CODE/scripts_py/resample_image.py
    """
    sz_in, sp_in, or_in, dir_in = img.GetSize(), img.GetSpacing(), img.GetOrigin(), img.GetDirection()
    scale = [spacing[i] / sp_in[i] for i in range(len(sp_in))]

    if not sz_out and not sp_out:
        sz_out, sp_out = [int(sz_in[i]/scale[i]) for i in range(len(sz_in))], [sp_in[i] * scale[i] for i in range(len(sp_in))]

    t = sitk.Transform(3, sitk.sitkScale)
    out_sitk = sitk.Resample(img, sz_out, t, sitk.sitkLinear, or_in, sp_out, dir_in, 0.0, sitk.sitkFloat32)

    return out_sitk, sz_out, sp_out


def avg_dice_distance(t1, t2, label_ids):

    if not label_ids:
        ulab = np.unique(np.concatenate((np.unique(t1), np.unique(t2)), axis=0))
        ulab = np.delete(ulab, np.where(ulab==0))
    else:
        ulab = np.array(label_ids)

    count = 0.
    for i_lab in ulab:
        count += dice(t1 == i_lab, t2 == i_lab)

    return count / float(ulab.size)


if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

print("Start program")
resample_size = (2.5,2.5,2.5)
sz_out = None
sp_out = None

# is command line method ?
method_cmdline = False
if args.method[0] in ['NormalizedCorrelation']:
    method_cmdline = True

# get file list
files_list = os.listdir(args.in_dir[0])
in_files_list = [f for f in files_list if fnmatch(f, '*' + args.in_suffix[0])]

assert in_files_list, "List of input files is empty"
in_dir = args.in_dir[0]

# get file list 2
if args.in2_dir is not None:
    files_list = os.listdir(args.in2_dir[0])
    in2_files_list = [f for f in files_list if fnmatch(f, '*' + args.in2_suffix[0])]
    assert in2_files_list, "List of input2 files is empty"
    in2_dir = args.in2_dir[0]
else:
    in2_files_list = in_files_list
    in2_dir = in_dir

# if command line method create temp dir and copy mask file
if method_cmdline:
    if os.path.exists(args.method[1]):
        rmtree(args.method[1],ignore_errors=True)
    if not os.path.exists(args.method[1]):
        os.makedirs(args.method[1])

    if args.mask_file is not None:
        copyfile(args.mask_file[0], os.path.join(args.method[1], os.path.basename(args.mask_file[0])))


scores = np.zeros((len(in_files_list), len(in2_files_list)), dtype=np.float32)

for i in range(len(in_files_list)):

    rid_index = in_files_list[i].find('_S_')
    RID_1 = in_files_list[i][rid_index-3:rid_index+7]
    sid_index = in_files_list[i].find('_S', rid_index+1)
    sampleid = in_files_list[i][sid_index+1:sid_index+7]
    sid_index_1 = in_files_list[i].find('_S', sid_index+1)
    if sid_index_1 == -1:
        sid_index_1 = sid_index
    sampleid_1 = in_files_list[i][sid_index_1+1:sid_index_1+7]
    
    if is_hpc:
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    if not method_cmdline:
        img1_sitk = sitk.ReadImage(os.path.join(in_dir, in_files_list[i]))
        if not sz_out:
            img_in_mm_space, sz_out, sp_out = resample_image(img1_sitk, resample_size)
        else:
            img_in_mm_space, _, _ = resample_image(img1_sitk, resample_size, sz_out, sp_out)
        img1 = sitk.GetArrayFromImage(img_in_mm_space)

        if args.mask_file is not None:
            mask_sitk = sitk.ReadImage(args.mask_file[0])
            mask = sitk.GetArrayFromImage(mask_sitk)
            assert img1.shape == mask.shape, "Target and mask images should be of same shape"
        else:
            mask = np.ones(img1.shape, dtype=np.bool)

    for i2 in range(len(in2_files_list)):

        print('File is ' + in_files_list[i2])
        rid_index = in_files_list[i2].find('_S_')
        RID_2 = in_files_list[i2][rid_index-3:rid_index+7]
        sid_index = in_files_list[i2].find('_S', rid_index+1)
        sampleid = in_files_list[i2][sid_index+1:sid_index+7]
        sid_index_2 = in_files_list[i2].find('_S', sid_index+1)
        if sid_index_2 == -1:
            sid_index_2 = sid_index
        sampleid_2 = in_files_list[i2][sid_index_2+1:sid_index_2+7]
        print('Extracted RID is ' + RID_2 + ' and extracted sampleid is ' + sampleid_2)


        print("Computing similarities for file {0} and {1}".format(RID_1 + '_' + sampleid_1, RID_2 + '_' + sampleid_2))


        if method_cmdline:
            tmp_dir = args.method[1]

            if args.method[0] == 'NormalizedCorrelation':
                imagemath_path = os.path.join(os.environ['ANTSPATH'], 'ImageMath')
                cmdline = [imagemath_path, '3', os.path.join(tmp_dir, 'dummy.txt'), 'NormalizedCorrelation']
                cmdline += [os.path.join(in_dir, in_files_list[i]), os.path.join(in2_dir, in2_files_list[i2])]
                if args.mask_file is not None:
                    cmdline += [os.path.join(tmp_dir, os.path.basename(args.mask_file[0]))]

            job_name = "{0}X{1}".format(RID_1 + '_' + sampleid_1, RID_2 + '_' + sampleid_2)
            qsub_launcher = Launcher(' '.join(cmdline))
            qsub_launcher.name = job_name
            qsub_launcher.folder = tmp_dir
            qsub_launcher.queue = "short.q"
            job_id = qsub_launcher.run()

            if is_hpc:
                wait_jobs += [job_id]

            n_jobs += 1
            list_of_jobs.append((job_name,i,i2))
            # Wait for the jobs to finish (in cluster)
            if is_hpc and n_total_jobs <= n_jobs:
                print("Waiting for registration jobs to finish...")
                call(wait_jobs)

                n_jobs = 0
                wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

                for (job_name,ii,ii2) in list_of_jobs:
                    out_file = os.path.join(tmp_dir, "{0}.out".format(job_name))

                    try:
                        check_file_repeat(out_file,10,10)
                    except:
                        print('Failed to read file {0}.out'.format(job_name))
                        continue

                    f = open(out_file)
                    try:
                        scores[ii, ii2] = float(f.read().lstrip('-'))
                    except:
                        scores[ii, ii2] = 0.0
                        print('Error in file {0}.out'.format(job_name))
                    f.close()
                    print('It works!')
                    err_file = os.path.join(tmp_dir, "{0}.err".format(job_name))
                    sh_file = os.path.join(tmp_dir, "{0}.sh".format(job_name))
                    
                    try:
                        os.remove(out_file)
                        os.remove(err_file)
                        os.remove(sh_file)
                    except:
                        pass

                list_of_jobs = []

        else:

            img2_sitk = sitk.ReadImage(os.path.join(in2_dir, in2_files_list[i2]))
            if not sz_out:
                img_in_mm_space, sz_out, sp_out = resample_image(img2_sitk, resample_size)
            else:
                img_in_mm_space, _, _ = resample_image(img2_sitk, resample_size, sz_out, sp_out)
            img2 = sitk.GetArrayFromImage(img_in_mm_space)
            assert img2.shape == img1.shape, "Target2 and target2 should be of same shape"

            a = img1[mask].ravel()
            b = img2[mask].ravel()

            if args.method[0] == 'Correlation':
                scores[i, i2] = 1. - correlation(a, b)

            elif args.method[0] == 'Dice':
                try:
                    scores[i, i2] = 1. - avg_dice_distance(a, b, args.method[1:])
                except:
                    scores[i, i2] = 1. - avg_dice_distance(a, b)


    # Wait for the last remaining jobs to finish (in cluster)
    if is_hpc:
        print("Waiting for registration jobs to finish...")
        call(wait_jobs)

        n_jobs = 0



    # Read scores when jobs are finished
    '''
    if method_cmdline:

        tmp_dir = args.method[1]

        if is_hpc:
            print("Waiting for similarity jobs to finish...")
            call(wait_jobs)

        for i2 in range(len(in2_files_list)):
            rid_index = in_files_list[i2].find('_S_')
            RID_2 = in_files_list[i2][rid_index-3:rid_index+7]
            sid_index = in_files_list[i2].find('_S', rid_index+1)
            sampleid = in_files_list[i2][sid_index+1:sid_index+7]
            sid_index_2 = in_files_list[i2].find('_S', sid_index+1)
            if sid_index_2 == -1:
                sid_index_2 = sid_index
            sampleid_2 = in_files_list[i2][sid_index_2+1:sid_index_2+7]
            
            out_file = os.path.join(tmp_dir, "{0}X{1}.out".format(RID_1 + '_' + sampleid_1, RID_2 + '_' + sampleid_2))

            try:
                check_file_repeat(out_file)
            except:
                print('Failed to read file {0}X{1}.out'.format(RID_1 + '_' + sampleid_1, RID_2 + '_' + sampleid_2))
                continue

            f = open(out_file)
            scores[i, i2] = float(f.read().lstrip('-'))
            f.close()

            err_file = os.path.join(tmp_dir, "{0}X{1}.err".format(RID_1 + '_' + sampleid_1, RID_2 + '_' + sampleid_2))
            sh_file = os.path.join(tmp_dir, "{0}X{1}.sh".format(RID_1 + '_' + sampleid_1, RID_2 + '_' + sampleid_2))
            
            try:
                os.remove(out_file)
                os.remove(err_file)
                os.remove(sh_file)
            except:
                pass
       '''
            
print("Finish!")
f = open(args.out_file[0], 'wb')
dump((in_dir, in_files_list, in2_dir, in2_files_list, scores), f)
f.close()

if method_cmdline:
    rmtree(args.method[1])






