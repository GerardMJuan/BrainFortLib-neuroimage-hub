"""
run ROBEX on a BIDS dataset.

ROBEX is a progrem that performs brain extraction on sMRI images.
"""

import bids.layout
import bids.tests
import os
from libs.scheduler import Launcher
import argparse
from fnmatch import fnmatch
from sys import platform
from subprocess import call

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir",type=str, nargs=1, required=True,help="dir of brain images (should contain ROBEX files too)")
parser.add_argument("--out_dir",type=str, nargs=1, required=True,help="output_dir")
parser.add_argument("--input_suffix",type=str, nargs=1, required=True,help="valid suffix for brain images")
parser.add_argument("--mask_suffix",type=str,help="whether to keep masks")
parser.add_argument("--number_jobs", type=int, nargs=1, required=True, help="Number of jobs for the cluster")

args = parser.parse_args()
n_jobs = 0
n_total_jobs = int(args.number_jobs[0])

os.environ["ANTSPATH"] = "/homedtic/gmarti/LIB/ANTsbin/bin"
os.environ["ANTSSCRIPTS"] = "/homedtic/gmarti/LIB/ANTs/Scripts"

# # Check platform

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

# Check that bids directory is not empty(TODO)
project_root = args.input_dir[0]
print(project_root)
layout = bids.layout.BIDSLayout([(project_root, 'bids')])
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Create img list
files = layout.get(extensions = args.input_suffix[0], modality = 'anat')

# create output directory
# output directory is of the form:
out_dir = args.out_dir[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '30']

for img in files:
    img_path = img.filename
    img_file = os.path.basename(img_path)
    img_name = img_file.split(args.input_suffix[0])[0]


    out_dir_img = out_dir + '/' + img.subject + '/' + img.session + '/' + img.modality + '/'
    if not os.path.exists(out_dir_img):
        os.makedirs(out_dir_img)

    strip_path = os.path.join(out_dir_img + img_file)

    # If the file exists at the output path, it already has been done
    if os.path.isfile(strip_path):
        continue

    # This needs to be changed
    if args.mask_suffix:
        mask_path = os.path.join(args.input_dir,img_names[i] + args.mask_suffix)
    else:
        mask_path = ''

    robex_path = os.path.join(os.environ['HOME'],'LIB','ROBEX')
    print("{}/runROBEX.sh {} {} {}".format(robex_path,img_path,strip_path,mask_path))
    qsub_launcher = Launcher("{}/runROBEX.sh {} {} {}".format(robex_path,img_path,strip_path,mask_path))
    qsub_launcher.name = img_name
    qsub_launcher.folder = out_dir_img
    qsub_launcher.queue = 'short'
    job_id = qsub_launcher.run()

    # break

    if is_hpc:
        wait_jobs += [job_id]

    n_jobs += 1

    # Wait for the jobs to finish (in cluster)
    if is_hpc and n_total_jobs <= n_jobs:
        print("Waiting for registration jobs to finish...")
        call(wait_jobs)

        # Put njobs and waitjobs at 0 again
        n_jobs = 0
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']


# Wait for the jobs to finish (in cluster)
if is_hpc:
    print("Waiting for registration jobs to finish...")
    call(wait_jobs)

print("Brain stripping finished.")
