import argparse
import os
from fnmatch import fnmatch
from scheduler import Launcher
from sys import platform
from subprocess import call
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description='Registers images to template. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='directory input images')
parser.add_argument("--in_metadata", type=str, nargs=1, required=True, help='input metadata')
parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix input images')
parser.add_argument("--template_file", type=str, nargs=1, required=True, help='template image')
parser.add_argument("--template_mask", type=str, nargs=1, help="(optional) to limit registration to a region (better start with good initialization)")
parser.add_argument("--init_warp_dir_suffix", type=str, nargs='+', action="append", help="(optional) dir, suffix (and inverse flag for affine) of warps to be used as initialization (in order)")
parser.add_argument("--transform", type=str, nargs=2, required=True, help="Rigid[*] | Affine[*] | Syn[*], 1<=resolution<=4 (with \'*\' do all lower resolutions too)")
parser.add_argument("--out_warp_intfix", type=str, nargs=1, required=True, help="intfix for output warps")
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='output directory for transformation files')
parser.add_argument("--output_warped_image", action="store_true", help="output warped images (image name w/o ext + intfix + Warped.nii.gz)")
parser.add_argument("--float", action="store_true", help='use single precision computations')
parser.add_argument("--use_labels", type=str, nargs='+', help='use labels for registration: label_dir, label_suffix, template_labels, [weights_list_for_each_stage]')
parser.add_argument("--clean", action="store_true", help="Clean out directory of output files")
parser.add_argument("--num_threads", type=int, nargs=1, default=[50], help="(optional) number of threads (default 50)")


os.environ["ANTSPATH"] = "/homedtic/gsanroma/CODE/LIB/ANTs/build/bin"

os.environ["ANTSSCRIPTS"] = "/homedtic/gsanroma/CODE/LIB/ANTs/Scripts"

args = parser.parse_args()

n_jobs = 0
n_total_jobs = int(args.num_threads[0])

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True
#
# Initial checks
#
#
# input directory
in_dir = args.in_dir[0]


# Get list of input images.
metadata = pd.read_csv(args.in_metadata[0])
img_list = metadata["MRI_PATH"].values
assert len(img_list), "List of input images is empty"

assert os.path.exists(args.template_file[0]), "Template file not found"
if args.template_mask is not None:
    assert os.path.exists(args.template_mask[0]), "Template mask not found"

if args.use_labels is not None:
    lab_list = [f.split(args.img_suffix[0])[0] + args.use_labels[1] for f in img_list]
    assert False not in [os.path.exists(os.path.join(args.use_labels[0], f)) for f in lab_list], "label files not found"
    assert os.path.exists(args.use_labels[2]), "Template labels not found"

resolution = int(args.transform[1])
assert resolution > 0 and resolution < 5, "Wrong resolution"

# create output directory
if not os.path.exists(args.out_dir[0]):
    os.makedirs(args.out_dir[0])

#
# Main loop
#

antsregistration_path = os.path.join(os.environ['ANTSPATH'], 'antsRegistration')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

for img_file in img_list:

    img_name = img_file.split(args.img_suffix[0])[0]
    img_path = args.in_dir[0] + img_file
    img_name = os.path.basename(img_name)
    print(img_file)

    if args.use_labels is not None:
        lab_path = os.path.join(args.use_labels[0], img_name + args.use_labels[1])
    weight_idx = 3

    cmdline = [antsregistration_path, '--dimensionality', '3']
    if args.output_warped_image:
        cmdline += ['--output', '[{}{},{}Warped.nii.gz]'.format(os.path.join(args.out_dir[0], img_name), args.out_warp_intfix[0], os.path.join(args.out_dir[0],img_name + args.out_warp_intfix[0]))]
    else:
        cmdline += ['--output', '{}{}'.format(os.path.join(args.out_dir[0], img_name), args.out_warp_intfix[0])]
    cmdline += ['--write-composite-transform', '0']
    cmdline += ['--collapse-output-transforms', '1']
    cmdline += ['--initialize-transforms-per-stage', '0']
    cmdline += ['--interpolation', 'Linear']
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

    smooth_sig = '4x2x1x0'
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

        cmdline += ['--convergence', '[{},1e-8,10]'.format('x'.join(its_linear))]
        cmdline += ['--smoothing-sigmas', smooth_sig]
        cmdline += ['--shrink-factors', shrink_fac]

    if args.transform[0].rstrip('*') == 'Affine' or (args.transform[0].rstrip('*') == 'Syn' and not args.init_warp_dir_suffix):

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

        cmdline += ['--convergence', '[{},1e-8,10]'.format('x'.join(its_linear))]
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

    #
    # mask

    if args.template_mask is not None:
        cmdline += ['--masks', args.template_mask[0]]

    #
    # launch

    print("Launching registration of file {}".format(img_name))
    #os.system(' '.join(cmdline))
    print(cmdline)

    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = img_name.split(os.extsep, 1)[0]
    qsub_launcher.folder = args.out_dir[0]
    # qsub_launcher.queue = 'short.q'
    job_id = qsub_launcher.run()

    if is_hpc:
        wait_jobs += [job_id]

    n_jobs += 1

    # Wait for the jobs to finish (in cluster)
    if is_hpc and n_total_jobs <= n_jobs:
        print("Waiting for registration jobs to finish...")
        call(wait_jobs)

        # Remove extra files from directory
        if args.clean:
            filelist = [ f for f in os.listdir(args.out_dir[0]) if (not f.endswith("Warped.nii.gz") and not f.endswith(".mat")) ]
            for f in filelist:
                os.remove(os.path.join(args.out_dir[0], f))

        # Put njobs and waitjobs at 0 again
        n_jobs = 0
        wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

# Wait for the last remaining jobs to finish (in cluster)
if is_hpc:
    print("Waiting for registration jobs to finish...")
    call(wait_jobs)

    ## Remove extra files from directory
    if args.clean:
        filelist = [ f for f in os.listdir(args.out_dir[0]) if (not f.endswith("Warped.nii.gz") and not f.endswith(".mat")) ]
        for f in filelist:
            os.remove(os.path.join(args.out_dir[0], f))

    # Put njobs at 0 again
    n_jobs = 0

print("Registration finished.")