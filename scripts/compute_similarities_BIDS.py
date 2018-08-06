#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compute similarities between pairs of images.

Given a dataset of .nii.gz images, compute pairs of similarities between them, with
different metrics.
"""

from bids.grabbids import BIDSLayout
import argparse
import os
from libs.scheduler import Launcher, check_file_repeat
from sys import platform
from subprocess import call
from shutil import rmtree, copyfile
import numpy as np
import SimpleITK as sitk
from scipy.spatial.distance import correlation, dice
from pickle import dump
import multiprocessing as mp
from multiprocessing import Queue
import time


parser = argparse.ArgumentParser()
parser.add_argument("--in_dir", type=str, nargs=1, required=True)
parser.add_argument("--img_suffix", type=str, nargs=1, required=True)
parser.add_argument("--mask_file", type=str, nargs=1, help="(optional) mask of region to compare")
parser.add_argument("--method", type=str, nargs='+', required=True, help='[Dice, [labels_list ...| nothing for all]] | Correlation | [NormalizedCorrelation, tmp_dir]')
parser.add_argument("--out_file", type=str, nargs=1, required=True, help="output file with pairwise similarities")
parser.add_argument("--number_jobs", type=int, nargs=1, required=True, help="Number of jobs for the cluster")
parser.add_argument("--number_cpus", type=int, nargs=1, required=True, help="Number of available cpus")

os.environ["ANTSPATH"] = "/homedtic/gmarti/LIB/ANTsbin/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gmarti/LIB/ANTs/Scripts"

args = parser.parse_args()

n_jobs = 0
n_total_jobs = int(args.number_jobs[0])

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

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


def parallel_dist(img_path_1, img_path_2, dist):
    """
    Auxiliar function to parallelize.

    This function takes 2 strings, representing a path to the two images to compare,
    and a keyword indicating the type of distance to compute.
    """
    # If the first parameter is None, don't do anything
    if not img_path_1:
        return 0
    img1_sitk = sitk.ReadImage(img_path_1)
    img2_sitk = sitk.ReadImage(img_path_2)

    resample_size = (1.5, 1.5, 1.5)
    sz_out = None
    sp_out = None

    if not sz_out:
        img_in_mm_space1, sz_out, sp_out = resample_image(img1_sitk, resample_size)
    else:
        img_in_mm_space1, _, _ = resample_image(img1_sitk, resample_size, sz_out, sp_out)

    if not sz_out:
        img_in_mm_space2, sz_out, sp_out = resample_image(img2_sitk, resample_size)
    else:
        img_in_mm_space2, _, _ = resample_image(img2_sitk, resample_size, sz_out, sp_out)

    img1 = sitk.GetArrayFromImage(img_in_mm_space1)
    img2 = sitk.GetArrayFromImage(img_in_mm_space2)
    try:
        assert img2.shape == img1.shape, "Target2 and target2 should be of same shape"
    except AssertionError:
        return 0

    a = img1.ravel()
    b = img2.ravel()

    if dist[0] == 'Correlation':
        scores = 1. - correlation(a, b)

    elif dist[0] == 'Dice':
        try:
            scores = 1. - avg_dice_distance(a, b, dist[1:])
        except:
            scores = 1. - avg_dice_distance(a, b)

    return scores

t0 = time.time()
project_root = args.in_dir[0]
print(project_root)
layout = BIDSLayout(project_root)
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Create img list
# Create subject list
files = layout.get(extensions='.nii.gz', modality='anat')

# is command line method ?
method_cmdline = False
if args.method[0] in ['NormalizedCorrelation']:
    method_cmdline = True

# if command line method create temp dir and copy mask file
if method_cmdline:
    if os.path.exists(args.method[1]):
        rmtree(args.method[1], ignore_errors=True)

    if not os.path.exists(args.method[1]):
        os.makedirs(args.method[1])

    if args.mask_file is not None:
        copyfile(args.mask_file[0], os.path.join(args.method[1], os.path.basename(args.mask_file[0])))

# Structure of results
scores = np.zeros((len(files), len(files)), dtype=np.float32)

# Parallelize loop
# l = len(files)
l = 10
if not method_cmdline:
    # Set number of cpus
    ncpus = args.number_cpus[0]
    # Initialize queue
    pool = mp.Pool(processes=ncpus)
    args_list = []
    for i in range(l):
        img_path = files[i].filename
        for j in range(i, l):
            img_path_2 = files[j].filename
            args_list.append((img_path, img_path_2, args.method))
            # args_list[j, i] = [img_path, img_path_2, args.method[0], (i,j)]

    scores_aux = pool.starmap(parallel_dist, args_list)
    k = 0
    for i in range(l):
        for j in range(i, l):
            scores[i, j] = scores_aux[k]
            k += 1

    scores = np.maximum(scores, scores.transpose())
    # Make the matrix symmetric


i = 0
# If normalized correlation
if method_cmdline:
    tmp_dir = args.method[1]
    list_of_jobs = []

    if is_hpc:
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    for img in files:
        img_path = img.filename
        img_file = os.path.basename(img_path)
        img_name = img_file.split(args.img_suffix[0])[0]

        for img2 in files:
            img_path_2 = img2.filename
            img_file_2 = os.path.basename(img_path_2)
            img_name_2 = img_file_2.split(args.img_suffix[0])[0]

        if args.method[0] == 'NormalizedCorrelation':
            imagemath_path = os.path.join(os.environ['ANTSPATH'], 'ImageMath')
            cmdline = [imagemath_path, '3', os.path.join(tmp_dir, 'dummy.txt'), 'NormalizedCorrelation']
            cmdline += [os.path.join(img_path, img_path_2)]
            if args.mask_file is not None:
                cmdline += [os.path.join(tmp_dir, os.path.basename(args.mask_file[0]))]

        job_name = "{0}X{1}".format(img.subject + '_' + img.session, img2.subject + '_' + img2.session)
        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = job_name
        qsub_launcher.folder = tmp_dir
        qsub_launcher.queue = "short.q"
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]

        n_jobs += 1
        list_of_jobs.append((job_name, i, j))
        # Wait for the jobs to finish (in cluster)
        if is_hpc and n_total_jobs <= n_jobs:
            print("Waiting for registration jobs to finish...")
            call(wait_jobs)

            n_jobs = 0
            wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

            for (job_name, i2, j2) in list_of_jobs:
                out_file = os.path.join(tmp_dir, "{0}.out".format(job_name))

                try:
                    check_file_repeat(out_file,10,10)
                except:
                    print('Failed to read file {0}.out'.format(job_name))
                    continue

                f = open(out_file)
                try:
                    scores[i2, j2] = float(f.read().lstrip('-'))
                except:
                    scores[i2, j2] = 0.0
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

print("Finish!")
f = open(args.out_file[0], 'wb')
file_list = [img.filename for img in files]
dump((project_root, file_list, scores), f)
f.close()

t1 = time.time()
print('Time to compute the script: ', t1 - t0)


if method_cmdline:
    rmtree(args.method[1])
