"""
Script that apply the cortical thickness pipeline of ANTS  to a set of images in a BIDS directory
and outputs and saves the results in the same folder.
This scripts uses the BIDS and CAPS neuroimaging folder structure.
"""

import bids.layout
import bids.tests
import argparse
import os
from fnmatch import fnmatch
from libs.scheduler import Launcher
from sys import platform
from subprocess import call
import numpy as np
import time
import pandas as pd

parser = argparse.ArgumentParser(description='Registers images to template. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='BIDS directory input images')
parser.add_argument("--in_name", type=str, nargs=1, help='derivative input directory')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix of input images')
parser.add_argument("--template_file", type=str, nargs=1, required=True, help='template image')
parser.add_argument("--out_name", type=str, nargs=1, required=True, help='Name of output image')
parser.add_argument("--metadata_file", type=str, nargs=1, help="(optional) list of subjects of which to compute the similarity")
parser.add_argument("--template_mask", type=str, nargs=1, help="(optional) to limit registration to a region (better start with good initialization)")
parser.add_argument("--init_warp_dir_suffix", type=str, nargs='+', action="append", help="(optional) dir, suffix (and inverse flag for affine) of warps to be used as initialization (in order)")
parser.add_argument("--transform", type=str, nargs=2, required=True, help="Rigid[*] | Affine[*] | Syn[*],BSplineSyN[*] 1<=resolution<=4 (with \'*\' do all lower resolutions too)")
parser.add_argument("--c_point", type=str, nargs=1, required=False, help='Spacing control points for BSpline transformation (optional)')
parser.add_argument("--out_warp_intfix", type=str, nargs=1, required=True, help="intfix for output warps")
parser.add_argument("--output_warped_image", action="store_true", help="output warped images (image name w/o ext + intfix + Warped.nii.gz)")
parser.add_argument("--float", action="store_true", help='use single precision computations')
parser.add_argument("--use_labels", type=str, nargs='+', help='use labels for registration: label_dir, label_suffix, template_labels, [weights_list_for_each_stage]')
parser.add_argument("--baseline", action="store_true", help="apply only to baseline images")
parser.add_argument("--number_jobs", type=int, nargs=1, required=True, help="Number of jobs for the cluster")

# Here add more things to the json info maybe?
# Output directory not needed, because it will be saved in the same input directory

os.environ["ANTSPATH"] = "/homedtic/gmarti/LIB/ANTsbin/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gmarti/LIB/ANTs/Scripts"


args = parser.parse_args()

n_jobs = 0
n_total_jobs = int(args.number_jobs[0])

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True
#
# Initial checks
#

# Check that bids directory is not empty
if args.in_name:
    project_root = args.in_dir[0] + 'derivatives/' + args.in_name[0]
else:
    project_root = args.in_dir[0]
print(project_root)
layout = bids.layout.BIDSLayout(project_root)
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Create img list
if args.baseline:
    files = layout.get(extensions='.nii.gz', modality='anat', session='M00')
else:
    files = layout.get(extensions='.nii.gz', modality='anat')

if args.metadata_file:
    new_files = []
    # Remove from files all the scans that do not appear in our metadata_file
    df_metadata = pd.read_csv(args.metadata_file[0])
    for f in files:
        s = f.subject
        PTID = s[4:7] + '_S_'+ s[8:]
        if PTID in df_metadata.PTID.values:
            new_files.append(f)
    files = new_files
    print("Number of scans")
    print(len(files))

# Checking template file
assert os.path.exists(args.template_file[0]), "Template file not found"
if args.template_mask is not None:
    assert os.path.exists(args.template_mask[0]), "Template mask not found"

# Other checks
if args.use_labels is not None:
    lab_list = [f.split(args.img_suffix[0])[0] + args.use_labels[1] for f in img_list]
    assert False not in [os.path.exists(os.path.join(args.use_labels[0], f)) for f in lab_list], "label files not found"
    assert os.path.exists(args.use_labels[2]), "Template labels not found"

resolution = int(args.transform[1])
assert resolution > 0 and resolution < 5, "Wrong resolution"

# If BSpline, need to be sure that
if args.transform[0].rstrip('*') == 'BSplineSyN':
    assert args.c_point[0], "Spacing control points not included"

# create output directory
# output directory is of the form: bids directory/derivatives/antsMNIspace/(TODO)
out_dir = args.in_dir[0] + 'derivatives/' + args.out_name[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Create json file indicating info about the script (TODO)

#
# Main loop
#
antsregistration_path = os.path.join(os.environ['ANTSPATH'], 'antsRegistration')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']

for img in files:
    img_path = img.filename
    img_file = os.path.basename(img_path)
    img_name = img_file.split(args.img_suffix[0])[0]

    # adapt out_dir to bids specification, copy part of the path of the input image
    # ha de ser out_dir + /sub/anat/
    session = os.path.basename(os.path.dirname(os.path.dirname(img_path)))
    out_dir_img = out_dir + '/' + img.subject + '/' + img.session + '/' + img.modality + '/'
    # out_dir_img = "/homedtic/gmarti/DATA/out_testing_spline2/"
    if not os.path.exists(out_dir_img):
        os.makedirs(out_dir_img)

    if args.use_labels is not None:
        lab_path = os.path.join(args.use_labels[0], img_name + args.use_labels[1])
    weight_idx = 3

    cmdline = [antsregistration_path, '--dimensionality', '3']
    if args.output_warped_image:
        cmdline += ['--output', '[{}{},{}Warped.nii.gz]'.format(os.path.join(out_dir_img, img_name), args.out_warp_intfix[0], os.path.join(out_dir_img, img_file.split(os.extsep, 1)[0] + args.out_warp_intfix[0]))]
    else:
        cmdline += ['--output', '{}{}'.format(os.path.join(out_dir_img, img_name), args.out_warp_intfix[0])]
    # cmdline += ['--write-composite-transform', '0']
    # cmdline += ['--collapse-output-transforms', '1']
    # cmdline += ['--initialize-transforms-per-stage', '0']
    # cmdline += ['--interpolation', 'Linear']
    cmdline += ['--use-histogram-matching', '1']

    if args.float:
        cmdline += ['--float', '1']

    #
    # init transforms

    if not args.init_warp_dir_suffix:
        cmdline += ['--initial-moving-transform', '[{},{},1]'.format(args.template_file[0], img_path)]
    else:
        for init_warp in args.init_warp_dir_suffix[::-1]:
            if len(init_warp) < 3:
                cmdline += ['--initial-moving-transform', os.path.join(init_warp[0], img_name + init_warp[1])]
            else:
                cmdline += ['--initial-moving-transform', '[{},{}]'.format(os.path.join(init_warp[0], img_name + init_warp[1]), init_warp[2])]

    #
    # transforms

    if args.transform[0][-1] == '*':  # use all resolutions
        its_linear = ['1000', '500', '250', '100'][:resolution] + ['0']*(4-resolution)
        its_syn = ['100', '100', '70', '20'][:resolution] + ['0']*(4-resolution)
    else:  # use only specified resolution
        its_linear = ['0']*(resolution - 1) + [['1000', '500', '250', '100'][resolution - 1]] + ['0'] * (4 - resolution)
        its_syn = ['0']*(resolution - 1) + [['100', '100', '70', '20'][resolution - 1]] + ['0'] * (4 - resolution)

    smooth_sig = '3x2x1x0'
    shrink_fac = '8x4x2x1'

    if args.transform[0].rstrip('*') == 'Rigid' or not args.init_warp_dir_suffix:

        cmdline += ['--transform', 'Rigid[0.1]']

        w_img, w_lab = 1.0, 0.0
        if args.use_labels is not None:
            if len(args.use_labels) > weight_idx:
                w_lab = float(args.use_labels[weight_idx])
            w_img = 1.0 - w_lab
            weight_idx += 1

        if not args.template_mask:
            cmdline += ['--metric', 'MI[{},{},{},32,Regular,0.25]'.format(args.template_file[0], img_path, w_img)]
        else:
            cmdline += ['--metric', 'GC[{},{},{}]'.format(args.template_file[0], img_path, w_img)]

        if w_lab > 0.0:
            cmdline += ['--metric', 'MeanSquares[{},{},{}]'.format(args.use_labels[2], lab_path, w_lab)]

        cmdline += ['--convergence', '[{}]'.format('x'.join(its_linear))]
        cmdline += ['--smoothing-sigmas', smooth_sig]
        cmdline += ['--shrink-factors', shrink_fac]

    if args.transform[0].rstrip('*') == 'Affine' or ((args.transform[0].rstrip('*') == 'Syn' or args.transform[0].rstrip('*') == 'BSplineSyN') and not args.init_warp_dir_suffix):

        cmdline += ['--transform', 'Affine[0.1]']

        w_img, w_lab = 1.0, 0.0
        if args.use_labels is not None:
            if len(args.use_labels) > weight_idx:
                w_lab = float(args.use_labels[weight_idx])
            w_img = 1.0 - w_lab
            weight_idx += 1

        if not args.template_mask:
            cmdline += ['--metric', 'MI[{},{},{},32,Regular,0.25]'.format(args.template_file[0], img_path, w_img)]
        else:
            cmdline += ['--metric', 'GC[{},{},{}]'.format(args.template_file[0], img_path, w_img)]

        if w_lab > 0.0:
            cmdline += ['--metric', 'MeanSquares[{},{},{}]'.format(args.use_labels[2], lab_path, w_lab)]

        cmdline += ['--convergence', '[{}]'.format('x'.join(its_linear))]
        cmdline += ['--smoothing-sigmas', smooth_sig]
        cmdline += ['--shrink-factors', shrink_fac]

    if args.transform[0].rstrip('*') == 'Syn':

        cmdline += ['--transform', 'SyN[0.1,3,0]']

        w_img, w_lab = 1.0, 0.0
        if args.use_labels is not None:
            if len(args.use_labels) > weight_idx:
                w_lab = float(args.use_labels[weight_idx])
            w_img = 1.0 - w_lab
            weight_idx += 1

        cmdline += ['--metric', 'CC[{},{},{},4]'.format(args.template_file[0], img_path, w_img)]
        if w_lab > 0.0:
            cmdline += ['--metric', 'MeanSquares[{},{},{}]'.format(args.use_labels[2], lab_path, w_lab)]

        cmdline += ['--convergence', '[{},1e-9,15]'.format('x'.join(its_syn))]
        cmdline += ['--smoothing-sigmas', smooth_sig]
        cmdline += ['--shrink-factors', shrink_fac]


    if args.transform[0].rstrip('*') == 'BSplineSyN':

        cmdline += ['--transform', 'BSplineSyN[0.1,' + args.c_point[0] + ',0]']

        w_img, w_lab = 1.0, 0.0
        if args.use_labels is not None:
            if len(args.use_labels) > weight_idx:
                w_lab = float(args.use_labels[weight_idx])
            w_img = 1.0 - w_lab
            weight_idx += 1

        cmdline += ['--metric', 'CC[{},{},{},4]'.format(args.template_file[0], img_path, w_img)]
        if w_lab > 0.0:
            cmdline += ['--metric', 'MeanSquares[{},{},{}]'.format(args.use_labels[2], lab_path, w_lab)]

        cmdline += ['--convergence', '[{},1e-9,15]'.format('x'.join(its_syn))]
        cmdline += ['--smoothing-sigmas', '3x2x1x0']
        cmdline += ['--shrink-factors', '6x4x2x1']

    # mask

    if args.template_mask is not None:
        cmdline += ['--masks', args.template_mask[0]]

    #
    # launch
    cmdline += ['-v','1']
    # print(' '.join(cmdline))
    print("Launching registration of file {}".format(img_file))

	#os.system(' '.join(cmdline))
    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_file.split(os.extsep, 1)[0]
    qsub_launcher.folder = out_dir_img
    qsub_launcher.queue = 'high'
    job_id = qsub_launcher.run()

    time.sleep(2)

    if is_hpc:
        wait_jobs += [job_id]

    n_jobs += 1

    # Wait for the jobs to finish (in cluster)
    if is_hpc and n_total_jobs <= n_jobs:
        print("Waiting for registration jobs to finish...")
        call(wait_jobs)

        # Remove extra files from directory
        # filelist = [ f for f in os.listdir(out_dir_img) if (not f.endswith(".nii.gz") and not f.endswith(".mat")) ]
        # for f in filelist:
        #     os.remove(os.path.join(out_dir_img, f))

        # Put njobs and waitjobs at 0 again
        n_jobs = 0
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']

# Wait for the last remaining jobs to finish (in cluster)
if is_hpc:
    print("Waiting for registration jobs to finish...")
    call(wait_jobs)

    ## Remove extra files from directory
    # filelist = [ f for f in os.listdir(out_dir_img) if (not f.endswith(".nii.gz") and not # f.endswith(".mat")) ]
    # for f in filelist:
    #   os.remove(os.path.join(out_dir_img, f))

    # Put njobs at 0 again
    n_jobs = 0

print("Registration finished.")
