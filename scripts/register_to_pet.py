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
parser.add_argument("--matrix_dir", type=str, nargs=1, required=True, help='template dir with all the baseline images')
parser.add_argument("--template_mask", type=str, nargs=1, help="(optional) to limit registration to a region (better start with good initialization)")
parser.add_argument("--init_warp_dir_suffix", type=str, nargs='+', action="append", help="(optional) dir, suffix (and inverse flag for affine) of warps to be used as initialization (in order)")
parser.add_argument("--out_warp_intfix", type=str, nargs=1, required=True, help="intfix for output warps")
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='output directory for transformation files')
parser.add_argument("--output_warped_image", action="store_true", help="output warped images (image name w/o ext + intfix + Warped.nii.gz)")
parser.add_argument("--float", action="store_true", help='use single precision computations')
parser.add_argument("--use_labels", type=str, nargs='+', help='use labels for registration: label_dir, label_suffix, template_labels, [weights_list_for_each_stage]')
parser.add_argument("--num_threads", type=int, nargs=1, default=[8], help="(optional) number of threads (default 8)")
parser.add_argument("--interpolation", type=str, nargs=1, required=True, help='interpolation: Linear, GenericLabel')
parser.add_argument("--mask", type=str, nargs=1, required=True, help='reference image: template mask')

# One of the arguments must be a directory with all the baselines, such that is easy to, given a followup, we can perform in a loop all the registrations with the correct

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

files_list = os.listdir(args.in_dir[0])
img_list = [f for f in files_list if fnmatch(f, '*' + args.img_suffix[0])]
assert img_list, "List of input images is empty"

assert os.path.exists(args.matrix_dir[0]), "Template file dir found"
if args.template_mask is not None:
    assert os.path.exists(args.template_mask[0]), "Template mask not found"

if args.use_labels is not None:
    lab_list = [f.split(args.img_suffix[0])[0] + args.use_labels[1] for f in img_list]
    assert False not in [os.path.exists(os.path.join(args.use_labels[0], f)) for f in lab_list], "label files not found"
    assert os.path.exists(args.use_labels[2]), "Template labels not found"


# create output directory
if not os.path.exists(args.out_dir[0]):
    os.makedirs(args.out_dir[0])

#
# Main loop
#


antsApplyTransforms_path = os.path.join(os.environ['ANTSPATH'], 'antsApplyTransforms')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '10']

    


for img_file in img_list:
    img_name = img_file.split(args.img_suffix[0])[0]
    
    # Find the template file in the baseline directory
    prefix_file = img_name[:15]
    
    files = [i for i in os.listdir(args.matrix_dir[0]) if (os.path.isfile(os.path.join(args.matrix_dir[0],i)) and \
         prefix_file in i and i.endswith(".mat" ))]
    

    template_file = os.path.join(args.matrix_dir[0],files[0])

    img_path = os.path.join(args.in_dir[0], img_file)

    if args.use_labels is not None:
        lab_path = os.path.join(args.use_labels[0], img_name + args.use_labels[1])
    weight_idx = 3
    cmdline = [antsApplyTransforms_path, '--dimensionality', '3']
    cmdline += ['--input-image-type', '3'] 
    cmdline += ['--input', '{}'.format(img_path)]
        
    if args.output_warped_image:
        cmdline += ['--output', '{}PETWarped.nii.gz'.format(os.path.join(args.out_dir[0], img_name), args.out_warp_intfix[0], os.path.join(args.out_dir[0], img_file.split(os.extsep, 1)[0] + args.out_warp_intfix[0]))]
    else:
        cmdline += ['--output', '{}{}'.format(os.path.join(args.out_dir[0], img_name), args.out_warp_intfix[0])]
    
    cmdline += ['--reference-image', '{}'.format(os.path.join(args.mask[0]))]
    cmdline += ['--interpolation', '{}'.format(args.interpolation[0])]
    cmdline += ['--transform','{}'.format(template_file)]
    
    if args.float:
        cmdline += ['--float', '1']

    
    #
    # mask

    if args.template_mask is not None:
        cmdline += ['--masks', args.template_mask[0]]

    #
    # launch

    print("Launching registration of file {}".format(img_file))
    # os.system(' '.join(cmdline))

    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_file.split(os.extsep, 1)[0]
    qsub_launcher.folder = args.out_dir[0]
    # qsub_launcher.omp_num_threads = args.num_threads[0]
    qsub_launcher.queue = 'short'
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
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSlurmJobs.pl"), '0', '60']

# Wait for the last remaining jobs to finish (in cluster)
if is_hpc:
    print("Waiting for registration jobs to finish...")
    call(wait_jobs)

    # Remove extra files from directory
    filelist = [ f for f in os.listdir(args.out_dir[0]) if not f.endswith(".nii.gz") ]
    for f in filelist:
         os.remove(os.path.join(args.out_dir[0], f))

    # Put njobs at 0 again
    n_jobs = 0

print("Registration finished.")
