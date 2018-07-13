"""
This script registers a set of tepmlate masks to their followups.

Scripts builds from propagate_mask_template.py
"""

from bids.grabbids import BIDSLayout
import argparse
import os
from fnmatch import fnmatch
from libs.scheduler import Launcher
from sys import platform
from subprocess import call
import numpy as np

parser = argparse.ArgumentParser(description='Registers images to template. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='BIDS directory input images')
parser.add_argument("--in_name", type=str, nargs=1, required=True, help='name of the derivative')
parser.add_argument("--reg_suffix", type=str, nargs=1, required=True, help='suffix of registration matrices')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix of input images')
parser.add_argument("--ref_name", type=str, nargs=1, required=True, help='Reference (og image) ')
parser.add_argument("--reg_name", type=str, nargs=1, required=True, help="dir where the transformation are")
parser.add_argument("--out_warp_intfix", type=str, nargs=1, required=True, help="intfix for output warps")

os.environ["ANTSPATH"] = "/homedtic/gmarti/LIB/ANTsbin/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gmarti/LIB/ANTs/Scripts"

n_jobs = 0
n_total_jobs = 10

args = parser.parse_args()

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

# Check that bids directory is not empty(TODO)
project_root = args.in_dir[0] + 'derivatives/' + args.in_name[0]
layout_img = BIDSLayout(project_root)
assert len(layout_img.get_subjects()) > 0, "No subjects in directory!"

# Create layout of the reference images
reference_root = args.in_dir[0] + 'derivatives/' + args.ref_name[0]
layout_ref = BIDSLayout(reference_root)
assert len(layout_ref.get_subjects()) > 0, "No subjects found in reference directory!"


project_root = args.in_dir[0] + 'derivatives/' + args.reg_name[0]
layout_reg = BIDSLayout(project_root)
assert len(layout_img.get_subjects()) > 0, "No registrations in directory!"


# Registrar cada template a un baseline corresponent
subjects = layout_img.get_subjects()

antsapptransform_path = os.path.join(os.environ['ANTSPATH'], 'antsApplyTransforms')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']

for s in subjects:

    # Get baseline mask
    files = layout_img.get(subject=s, session='M00', extensions='.nii.gz')
    assert len(files) > 0, "Subject " + s + " has no mask!"
    baseline = files[0]
    baseline_mask = baseline.filename

    # Get list of all subjects
    files = layout_reg.get(subject=s, extensions='.nii.gz')
    for img in files:
        if img.session == baseline.session:
            # If baseline is the same, remove it
            continue

        img_path = img.filename
        if not img_path.endswith(args.img_suffix[0]):
            continue
        img_file = os.path.basename(img_path)
        img_name = img_file.split(args.img_suffix[0])[0]

        # Create references images
        files = layout_ref.get(subject=img.subject, session=img.session, extensions='.nii.gz')
        assert len(files) > 0, "Subject " + s + " has no reference_img!"
        ref_img = files[0]

        # Check if transformation matrix exists
        t_name_aff = img_path.split(args.img_suffix[0])[0] + args.reg_suffix[0]
        assert os.path.isfile(t_name_aff), t_name_aff + " has no registration file in its directory!"

        # Check if transformation matrix exists
        # t_name_syn = img_path.split(args.img_suffix[0])[0] + '1InverseWarp.nii.gz'
        # assert os.path.isfile(t_name_syn), t_name_syn + " has no registration file in its directory!"

        # adapt out_dir to bids specification, copy part of the path of the input image
        # ha de ser out_dir + /sub/anat/
        session = os.path.basename(os.path.dirname(os.path.dirname(img_path)))

        # Out path is the same as in dir
        out_dir_img = args.in_dir[0] + 'derivatives/' + args.in_name[0] + '/' + img.subject + '/' + img.session + '/' + img.modality + '/'
        if not os.path.exists(out_dir_img):
            os.makedirs(out_dir_img)

        # Create the command
        cmdline = [antsapptransform_path, '--dimensionality', '3']
        cmdline += ['--input', baseline_mask]
        cmdline += ['--reference-image', ref_img.filename]
        cmdline += ['--output', '{}{}.nii.gz'.format(os.path.join(out_dir_img, img_name), args.out_warp_intfix[0])]
        cmdline += ['--interpolation', 'BSpline']
        cmdline += ['--transform', '[' + t_name_aff + ',1]']
        # cmdline += ['--transform', t_name_syn]
        # print(' '.join(cmdline))
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
    # filelist = [ f for f in os.listdir(out_dir_img) if (not f.endswith(".nii.gz") and not f.endswith(".mat")) ]
    # for f in filelist:
    #   os.remove(os.path.join(out_dir_img, f))

    # Put njobs at 0 again
    n_jobs = 0

print("Registration finished.")
