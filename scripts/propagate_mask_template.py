"""
This script registers a template mask to a given set of MRI images
using a previously computed registration.
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

parser = argparse.ArgumentParser(description='Registers images to template. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='BIDS directory input images')
parser.add_argument("--in_name", type=str, nargs=1, required=True, help='derivatives directory input name')
parser.add_argument("--reg_suffix", type=str, nargs=1, required=True, help='suffix of registration matrices')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix of registration matrices')
parser.add_argument("--out_name", type=str, nargs=1, required=True, help='Name of output image')
parser.add_argument("--ref_name", type=str, nargs=1, required=True, help='Reference (og image) ')
parser.add_argument("--template_mask", type=str, nargs=1, required=True, help="mask to register")
parser.add_argument("--number_jobs", type=int, nargs=1, required=True, help="Number of jobs for the cluster")
parser.add_argument("--out_warp_intfix", type=str, nargs=1, required=True, help="intfix for output mask")

os.environ["ANTSPATH"] = "/homedtic/gmarti/LIB/ANTsbin/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gmarti/LIB/ANTs/Scripts"

n_jobs = 0
n_total_jobs = 10

args = parser.parse_args()

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

#
# Initial checks
#

# Check that bids directory is not empty
project_root = args.in_dir[0] + 'derivatives/' + args.in_name[0]
print(project_root)
layout_img = bids.layout.BIDSLayout(project_root)
assert len(layout_img.get_subjects()) > 0, "No subjects in directory!"

# Create layout of the reference images
reference_root = args.in_dir[0] + 'derivatives/' + args.ref_name[0]
layout_ref = bids.layout.BIDSLayout(reference_root)
assert len(layout_ref.get_subjects()) > 0, "No subjects found in reference directory!"

# Checking template file
assert os.path.exists(args.template_mask[0]), "Template mask not found"

# Registrar cada template a un baseline corresponent
files = layout_img.get(extensions='.nii.gz', modality='anat', session='M00')

antsapptransform_path = os.path.join(os.environ['ANTSPATH'], 'antsApplyTransforms')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']

out_dir = args.in_dir[0] + 'derivatives/' + args.out_name[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

for img in files:
    img_path = img.filename
    print(img_path)
    if not img_path.endswith(args.img_suffix[0]):
        continue
    img_file = os.path.basename(img_path)
    img_name = img_file.split(args.img_suffix[0])[0]
    # Check if transformation matrix exists
    t_name_aff = img_path.split(args.img_suffix[0])[0] + args.reg_suffix[0]
    assert os.path.isfile(t_name_aff), t_name_aff + " has no registration file in its directory!"
    # Check if transformation matrix exists
    t_name_syn = img_path.split(args.img_suffix[0])[0] + '1InverseWarp.nii.gz'
    assert os.path.isfile(t_name_syn), t_name_syn + " has no registration file in its directory!"

    # Create references images
    files = layout_ref.get(subject=img.subject, session=img.session, extensions='.nii.gz')
    assert len(files) > 0, "Subject " + s + " has no reference_img!"
    ref_img = files[0]

    # adapt out_dir to bids specification, copy part of the path of the input image
    # ha de ser out_dir + /sub/anat/
    session = os.path.basename(os.path.dirname(os.path.dirname(img_path)))
    out_dir_img = out_dir + '/' + img.subject + '/' + img.session + '/' + img.modality + '/'
    if not os.path.exists(out_dir_img):
        os.makedirs(out_dir_img)

    # Create the command
    cmdline = [antsapptransform_path, '--dimensionality', '3']
    cmdline += ['--input', args.template_mask[0]]
    cmdline += ['--reference-image', ref_img.filename]
    cmdline += ['--output', '{}{}.nii.gz'.format(os.path.join(out_dir_img, img_name), args.out_warp_intfix[0])]
    cmdline += ['--interpolation', 'BSpline']
    cmdline += ['--transform', '[' + t_name_aff + ',1]']
    cmdline += ['--transform', t_name_syn]

    print(' '.join(cmdline))
    print("Launching registration of file {}".format(img_file))

	#os.system(' '.join(cmdline))
    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_file.split(os.extsep, 1)[0]
    qsub_launcher.folder = out_dir_img
    qsub_launcher.queue = 'medium'
    job_id = qsub_launcher.run()

    if is_hpc:
        wait_jobs += [job_id]

    n_jobs += 1

    # Wait for the jobs to finish (in cluster)
    if is_hpc and n_total_jobs <= n_jobs:
        print("Waiting for registration jobs to finish...")
        call(wait_jobs)

        # Remove extra files from directory
        # filelist = [f for f in os.listdir(out_dir_img) if (not f.endswith(".nii.gz") and not f.endswith(".mat")) ]
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
    # filelist = [ f for f in os.listdir(out_dir_img) if (not f.endswith(".nii.gz") and not f.endswith(".mat")) ]
    # for f in filelist:
    #   os.remove(os.path.join(out_dir_img, f))

    # Put njobs at 0 again
    n_jobs = 0

print("Registration finished.")
