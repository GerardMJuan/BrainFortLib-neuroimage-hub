"""
This script applies several steps of preprocessing to a list of ADNI files.

From a metadata file with the paths of the images, it process each image
separately and saves the image in the same directory, with an added prefix.

In the preprocessing pipeline, this is always the first step.
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

parser = argparse.ArgumentParser(description='Processes the images including N4 correction and histogram matching to template.\n'
                                             'Optionally, images and/or template can be masked out (e.g., remove skull) given the mask file.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='Parent ADNI directory')
parser.add_argument("--in_metadata", type=str, nargs=1, required=True, help='input metadata')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix input images')
parser.add_argument("--n4", action="store_true", help="N4 bias correction")
parser.add_argument("--denoising", action="store_true", help="Denoising")
parser.add_argument("--histmatch", action="store_true", help="histogram matching (needs template)")
parser.add_argument("--template_file", type=str, nargs=1, help="template image")
parser.add_argument("--template_norm", action="store_true", help="normalize template intensities between [0..1]")
parser.add_argument("--out_dir", type=str, nargs=1, help='Output ADNI directory.')
parser.add_argument("--clean", action="store_true", help="Clean out directory of output files")
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

if not args.histmatch:
    assert args.template_file is None and args.template_maskout_mask is None and not args.template_norm, "Unnecessary template if not histmatch"

if args.histmatch:
    assert args.template_file is not None, "Need template for histogram matching"

if args.template_file is not None:
    assert os.path.exists(args.template_file[0]), "Template file not found"

# Get list of input images.
metadata = pd.read_csv(args.in_metadata[0])
img_list = metadata["MRI_PATH"].values
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
# N4 Bias Field Correction.
if args.n4:

    n4_path = os.path.join(os.environ['ANTSPATH'], 'N4BiasFieldCorrection')
    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    for img_file in img_list:
        # The output path is in the out_dir, following the same structure as
        # the output.
        out_path = os.path.join(args.out_dir[0], img_file)

        if not os.path.exists(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))

        cmdline = [n4_path, '--image-dimensionality', '3']
        cmdline += ['--input-image', os.path.join(in_dir, img_file)]
        cmdline += ['--shrink-factor', '3']
        cmdline += ['--convergence', '50x50x30x20', '1e-6']
        cmdline += ['--bspline-fitting', '300']
        cmdline += ['--output', out_path]

        print("Launching N4 for {}".format(img_file))

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = os.path.splitext(os.path.basename(img_file))[0]
        qsub_launcher.folder = os.path.dirname(out_path)
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

    print("N4 finished.")
    # assign input directory for subsequent steps
    in_dir = args.out_dir[0]
    njobs = 0

if args.denoising:

    denoise_path = os.path.join(os.environ['ANTSPATH'], 'DenoiseImage')
    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']

    for img_file in img_list:
        # The output path is in the out_dir, following the same structure as
        # the output.
        out_path = os.path.join(args.out_dir[0], img_file)

        if not os.path.exists(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))

        cmdline = [denoise_path, '--image-dimensionality', '3']
        cmdline.extend(['--input-image', os.path.join(in_dir, img_file)])
        cmdline.extend(['--noise-model', 'Rician'])
        cmdline += ['--output', out_path]

        print("Launching Denoising for {}".format(img_file))

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = os.path.splitext(os.path.basename(img_file))[0]
        qsub_launcher.folder = os.path.dirname(out_path)
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

    print("Denoising finished.")
    # assign input directory for subsequent steps
    in_dir = args.out_dir[0]
    njobs = 0


if args.histmatch:
    # process template

    if args.template_norm:

        print("Processing template")

        template_sitk = sitk.ReadImage(args.template_file[0])
        template = sitk.GetArrayFromImage(template_sitk)

        template = (template - template.min()) / (template.max() - template.min())

        aux = sitk.GetImageFromArray(template)
        aux.CopyInformation(template_sitk)
        sitk.WriteImage(aux, args.template_file[0]+'_norm.nii')

    imagemath_path = os.path.join(os.environ['ANTSPATH'],'ImageMath')
    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    for img_file in img_list:
        # The output path is in the out_dir, following the same structure as
        # the output.

        in_file = os.path.join(in_dir, img_file)
        out_file = os.path.join(args.out_dir[0], img_file)
        tpl_file = args.template_file[0]+'_norm.nii'

        if not os.path.exists(os.path.dirname(out_path)):
            os.makedirs(os.path.dirname(out_path))

        cmdline = [imagemath_path, '3', out_file, 'HistogramMatch', in_file, tpl_file]

        print("Launching histogram match of {}".format(img_file))

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = os.path.splitext(os.path.basename(img_file))[0]
        qsub_launcher.folder = os.path.dirname(out_path)
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

    print("Histogram matching finished.")
