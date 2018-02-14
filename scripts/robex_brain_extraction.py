
import os
from scheduler import Launcher
import argparse
from fnmatch import fnmatch
from sys import platform
from subprocess import call

parser = argparse.ArgumentParser()
parser.add_argument("input_dir",type=str,help="dir of brain images (should contain ROBEX files too)")
parser.add_argument("input_suffix",type=str,help="valid suffix for brain images")
parser.add_argument("strip_suffix",type=str,help="suffix to be added to stripped images")
parser.add_argument("--mask_suffix",type=str,help="whether to keep masks")

args = parser.parse_args()
# args = parser.parse_args(['/Users/gsanroma/DATA/DATABASES/ADNI/img','_brain_denoised.nii','_strip.nii.gz','--mask_suffix','_mask.nii.gz'])

# assert os.path.exists(os.path.join(args.input_dir,'ROBEX')) and \
#        os.path.exists(os.path.join(args.input_dir,'ref_vols')) and \
#        os.path.exists(os.path.join(args.input_dir,'dat')), "ROBEX files not found in {}".format(args.input_dir)

#
# # Check platform

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

#
# # Check platform

files_list = os.listdir(args.input_dir)
img_files = [f for f in files_list if fnmatch(f, '*' + args.input_suffix)]
img_names = [f.strip(args.input_suffix) for f in img_files]
assert img_files, "List of images is empty"

wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '30']

for i in range(len(img_files)):

    input_path = os.path.join(args.input_dir,img_files[i])
    strip_path = os.path.join(args.input_dir,img_names[i] + args.strip_suffix)
    if args.mask_suffix:
        mask_path = os.path.join(args.input_dir,img_names[i] + args.mask_suffix)
    else:
        mask_path = ''

    robex_path = os.path.join(os.environ['HOME'],'programs','ROBEX','build')

    print "Brain extraction of {}".format(img_files[i])
    qsub_launcher = Launcher("{}/ROBEX {} {} {}".format(robex_path,input_path,strip_path,mask_path))
    qsub_launcher.name = img_names[i]
    qsub_launcher.folder = args.input_dir
    qsub_launcher.queue = 'short.q'
    job_id = qsub_launcher.run()

    # break

    if is_hpc:
        wait_jobs += [job_id]

# Wait for the jobs to finish (in cluster)
if is_hpc:
    print "Waiting for brain stripping jobs to finish..."
    call(wait_jobs)
print "Brain stripping finished."




