"""
Script to register all images to a given template.abs

This scripts uses the BIDS and CAPS neuroimaging folder structure.
"""

from bids.grabbids import BIDSLayout
import argparse
import os
from fnmatch import fnmatch
from scheduler import Launcher
from sys import platform
from subprocess import call
import pandas as pd
import numpy as np

parser = argparse.ArgumentParser(description='Registers images to template. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='BIDS directory input images')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix of input images')
parser.add_argument("--output_path", type=str, nargs=1, help="(optional) to limit registration to a region (better start with good initialization)")
parser.add_argument("--subject_file", type=str, nargs=1, required=True, help="file detailing the subjects that need to be included in the file.")
parser.add_argument("--number_jobs", type=int, nargs=1, required=True, help="Number of jobs for the cluster")

args = parser.parse_args()

n_jobs = 0
n_total_jobs = args.number_jobs[0]


if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True
#
# Initial checks
#
os.environ["ANTSPATH"] = "/homedtic/gmarti/LIB/ANTsbin/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gmarti/LIB/ANTs/Scripts"


# Check that bids directory is not empty(TODO)
project_root = args.in_dir[0]
layout = BIDSLayout(project_root)
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Create img list
files = layout.get(extensions='.nii.gz', modality='anat', session='M00')
# Keep only the baselines and the files from the subject_file
df_subjects = pd.read_csv(args.subject_file[0])
files_true = [x for x in layout.get_subjects() if str(x[4:7] + "_S_" + x[8:12]) in df_subjects.PTID.values]
print(len(files))
print(len(files_true))

# create output directory
out_dir = args.output_path[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Create json file indicating info about the script (TODO)
# This i dunnot know

#
# Main loop
#
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']

for img in files:
    if img.subject not in files_true:
        continue
    """
    if os.path.exists(out_dir + '/' + img.subject):
        # If already processed, continue
        continue
    """
    img_path = img.filename
    img_file = os.path.basename(img_path)
    img_name = img_file.split(args.img_suffix[0])[0]
    # adapt out_dir to bids specification, copy part of the path of the input image
    # ha de ser out_dir + /sub/anat/
    cmdline = ['recon-all', '-i', img_path, '-subjid', img.subject, '-sd', out_dir, '-all', '-no-isrunning']

    # cmdline = ['recon-all', '-subjid', img.subject, '-sd', out_dir, '-all', '-no-isrunning']

    print(' '.join(cmdline))
    print("Launching registration of file {}".format(img_file))

    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_file.split(os.extsep, 1)[0]
    qsub_launcher.folder = out_dir
    qsub_launcher.queue = 'high'
    job_id = qsub_launcher.run()

    if is_hpc:
        wait_jobs += [job_id]

    n_jobs += 1

    # Wait for the jobs to finish (in cluster)
    if is_hpc and n_total_jobs <= n_jobs:
        print("Waiting for jobs to finish...")
        call(wait_jobs)

        # Put njobs and waitjobs at 0 again
        n_jobs = 0
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']


# Wait for the last remaining jobs to finish (in cluster)
if is_hpc:
    print("Waiting for jobs to finish...")
    call(wait_jobs)

    # Put njobs at 0 again
    n_jobs = 0

print("Freesurfer recon-all finished.")
