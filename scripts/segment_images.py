"""
This script segments a set of MRI images.

This script segments the image into GM, WM and CSF parts.
"""

import argparse
from fnmatch import fnmatch
from scheduler import Launcher
from sys import platform
from subprocess import call
import os
import SimpleITK as sitk
import numpy as np
from shutil import copyfile
import pandas as pd

parser = argparse.ArgumentParser(description='Segment a set of images.\n'
                                             'Images should not have a skull.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='Parent ADNI directory')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix input images')
parser.add_argument("--out_dir", type=str, nargs=1, help='Output ADNI directory.')
parser.add_argument("--num_threads", type=int, nargs=1, default=[50], help="(optional) number of threads (default 50)")

os.environ["ANTSPATH"] = "/homedtic/gsanroma/CODE/LIB/ANTs/build/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gsanroma/CODE/LIB/ANTs/Scripts"

args = parser.parse_args()

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

#
# Initial checks
#
n_total_jobs = int(args.num_threads[0])
in_dir = args.in_dir[0]
img_suffix = args.img_suffix[0]
# Get list of input images.
files_list = os.listdir(in_dir)
img_list = [f for f in sorted(files_list) if fnmatch(f, '*' + img_suffix)]
assert len(img_list), "List of input images is empty"

# control number of jobs
njobs = 0

# input directory
in_dir = args.in_dir[0]

# create output directory
if not os.path.exists(args.out_dir[0]):
    os.makedirs(args.out_dir[0])

#
# Pipeline
#
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

for img_file in img_list:
    # The output path is in the out_dir, following the same structure as
    # the output.
    out_path = os.path.join(args.out_dir[0], img_file)

    if not os.path.exists(os.path.dirname(out_path)):
        os.makedirs(os.path.dirname(out_path))
    fastpath = '/homedtic/gmarti/fsl-lib/bin/fast'
    cmdline = [fastpath]
    cmdline += ['-n 3'] #Number of classes
    cmdline += ['-o', out_path] #Number of classes
    cmdline += [os.path.join(in_dir, img_file)] # File
    print("Launching segmentation for {}".format(img_file))

    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_file.split(os.extsep, 1)[0]
    qsub_launcher.folder = args.out_dir[0]
    qsub_launcher.queue = 'short.q'
    job_id = qsub_launcher.run()
    njobs = njobs + 1
    if is_hpc:
        wait_jobs += [job_id]

    if is_hpc and njobs >= n_total_jobs:
        print("Limit found. Wait for jobs to finish...")
        call(wait_jobs)
        njobs = 0
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

if is_hpc:
    print("Waiting for remaining jobs to finish...")
    call(wait_jobs)

print("Segmentation finished.")
# assign input directory for subsequent steps
njobs = 0
