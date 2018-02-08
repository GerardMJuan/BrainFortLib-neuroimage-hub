
import argparse
import os
from fnmatch import fnmatch
from scheduler import Launcher
from sys import platform
from subprocess import call
import numpy as np

parser = argparse.ArgumentParser(description='Registers images to template. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='directory input images')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix input images')
parser.add_argument("--template_dir", type=str, nargs=1, required=True, help='template dir with all the baseline images')
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='output directory for transformation files')
parser.add_argument("--matrix", type=str, nargs=1, required=True, help='matrix from Affine MRI registration')
parser.add_argument("--out_warp_intfix", type=str, nargs=1, required=True, help="intfix for output warps")


# One of the arguments must be a directory with all the baselines, such that is easy to, given a followup, we can perform in a loop all the registrations with the correct

os.environ["ANTSPATH"] = "/hpc_old/gsanroma/CODE/LIB/ANTs/build/bin"

os.environ["ANTSSCRIPTS"] = "/hpc_old/gsanroma/CODE/LIB/ANTs/Scripts"

args = parser.parse_args()

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

is_hpc = False
n_jobs = 0
n_total_jobs = 80



#
# Initial checks
#

files_list = os.listdir(args.in_dir[0])
img_list = [f for f in files_list if fnmatch(f, '*' + args.img_suffix[0])]
assert img_list, "List of input images is empty"
assert os.path.exists(args.template_dir[0]), "Template file dir found"



#
# Main loop
#

antsApplyTransforms_path = os.path.join(os.environ['ANTSPATH'], 'antsApplyTransforms')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

for img_file in img_list:
    img_name = img_file.split(args.img_suffix[0])[0]
    cmdline = [antsApplyTransforms_path, '--dimensionality', '3']
    
   
    cmdline += ['--output', '{}{}.nii.gz'.format(os.path.join(args.out_dir[0], img_name), args.out_warp_intfix[0])] 
    cmdline += ['--input', '{}{}'.format(os.path.join(args.in_dir[0], img_name), args.img_suffix[0])]
    cmdline += ['--input-image-type', '3'] 
    cmdline += ['--interpolation', 'Linear']
    cmdline += ['--reference-image', '{}'.format(os.path.join(args.template_dir[0]))]
    cmdline += ['--transform','{}'.format(os.path.join(args.matrix[0]))]
    
    
    # launch
    
    print("Launching registration of file {}".format(img_file))
    # os.system(' '.join(cmdline))
    
    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_file.split(os.extsep, 1)[0]
    qsub_launcher.folder = args.out_dir[0]
    #qsub_launcher.omp_num_threads = args.num_threads[0]
    # qsub_launcher.queue = 'short.q'
    job_id = qsub_launcher.run()
    
    if is_hpc:
        wait_jobs += [job_id]
    
    n_jobs += 1
    
    # Wait for the jobs to finish (in cluster)
    if is_hpc and n_total_jobs <= n_jobs:
        print("Waiting for registration jobs to finish...")
        call(wait_jobs)
    
        ## Remove extra files from directory
        filelist = [ f for f in os.listdir(args.out_dir[0]) if not f.endswith(".nii.gz") ]
        for f in filelist:
            os.remove(os.path.join(args.out_dir[0], f))
    
        # Put njobs and waitjobs at 0 again
        n_jobs = 0
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']

# Wait for the last remaining jobs to finish (in cluster)
if is_hpc:
    print("Waiting for registration jobs to finish...")
    call(wait_jobs)

    # Remove extra files from directory
    #filelist = [ f for f in os.listdir(args.out_dir[0]) if not f.endswith(".nii.gz") ]
    #for f in filelist:
    #     os.remove(os.path.join(args.out_dir[0], f))

    # Put njobs at 0 again
    n_jobs = 0

print("Registration finished.")

