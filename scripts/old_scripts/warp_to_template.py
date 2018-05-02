import argparse
import os
from fnmatch import fnmatch
from scheduler import Launcher
from sys import platform
from subprocess import call

parser = argparse.ArgumentParser(description='Warp images to template space. Optionally, the inverse transformation can be done')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help="dir with input images (native). If inverse with additional args, then dir images in template space.")
parser.add_argument("--linear_suffix", type=str, nargs=1, action="append", help="suffix of images to be interpolated with linear")
parser.add_argument("--nearest_suffix", type=str, nargs=1, action="append", help="suffix of images to be interpolated with nn")
parser.add_argument("--template_file", type=str, nargs=1, required=True, help='template image')
parser.add_argument("--reg_dir", type=str, nargs=1, required=True, help='directory with transformations from input images to template')
parser.add_argument("--in_linear_intfix", type=str, nargs=1, required=True, help="intfix of the input linear transform")
parser.add_argument("--in_deform_intfix", type=str, nargs=1, help="(optional) intfix of the input deformation field")
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='output directory')
parser.add_argument("--out_suffix", type=str, nargs=1, required=True, help="suffix to be added to the filename without extension")
parser.add_argument("--inverse", type=str, nargs='*', help="(optional) [ no args : template -> subjects | dir_native suffix : template space -> native space ] (beware of interpolation trick!)")
parser.add_argument("--float", action="store_true")

args = parser.parse_args()

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

if args.linear_suffix is None:
    args.linear_suffix = []
if args.nearest_suffix is None:
    args.nearest_suffix = []

files_list = os.listdir(args.in_dir[0])
linear_superlist = [[f for f in files_list if fnmatch(f, '*' + args.linear_suffix[i][0])] for i in range(len(args.linear_suffix))]
nearest_superlist = [[f for f in files_list if fnmatch(f, '*' + args.nearest_suffix[i][0])] for i in range(len(args.nearest_suffix))]

# create output directory
if not os.path.exists(args.out_dir[0]):
    os.makedirs(args.out_dir[0])

if args.inverse is None:
    print "Warping each subject to template"
elif len(args.inverse) == 0:
    print "Warping template to each subject"
else:
    print "Warping subjects in template space to native space"
    native_linear_superlist = [[f.split(args.linear_suffix[i][0])[0] + args.inverse[1] for f in linear_superlist[i]] for i in range(len(args.linear_suffix))]
    native_nearest_superlist = [[f.split(args.nearest_suffix[i][0])[0] + args.inverse[1] for f in nearest_superlist[i]] for i in range(len(args.nearest_suffix))]
    for native_linear_list in native_linear_superlist:
        assert False not in [os.path.exists(os.path.join(args.inverse[0], f)) for f in native_linear_list], "Subject file in template space to be inverted not found"
    for native_nearest_list in native_nearest_superlist:
        assert False not in [os.path.exists(os.path.join(args.inverse[0], f)) for f in native_nearest_list], "Subject file in template space to be inverted not found"

antsapplytransforms_path = os.path.join(os.environ['ANTSPATH'], 'antsApplyTransforms')
wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

for files_list, suffix, interpolation in zip(linear_superlist, args.linear_suffix, ['Linear']*len(args.linear_suffix)) + \
        zip(nearest_superlist, args.nearest_suffix, ['NearestNeighbor']*len(args.nearest_suffix)):

    for file in files_list:

        cmdline = [antsapplytransforms_path, '--dimensionality', '3']
        cmdline += ['--interpolation', interpolation]
        cmdline += ['--default-value', '0']
        if args.float:
            cmdline += ['--float']

        file_name = file.split(suffix[0])[0]

        if args.inverse is None:

            cmdline += ['--input', os.path.join(args.in_dir[0], file)]
            cmdline += ['--reference-image', args.template_file[0]]

            if args.in_deform_intfix is not None:
                cmdline += ['--transform', os.path.join(args.reg_dir[0], file_name + args.in_deform_intfix[0] + '1Warp.nii.gz')]
            cmdline += ['--transform', os.path.join(args.reg_dir[0], file_name + args.in_linear_intfix[0] + '0GenericAffine.mat')]

        elif len(args.inverse) == 0:

            cmdline += ['--input', args.template_file[0]]
            cmdline += ['--reference-image', os.path.join(args.in_dir[0], file)]

            cmdline += ['--transform', '[{},1]'.format(
                os.path.join(args.reg_dir[0], file_name + args.in_linear_intfix[0] + '0GenericAffine.mat'))]
            if args.in_deform_intfix is not None:
                cmdline += ['--transform', os.path.join(args.reg_dir[0], "{}1InverseWarp.nii.gz".format(
                    file_name + args.in_deform_intfix[0]))]

        else:

            cmdline += ['--input', os.path.join(args.in_dir[0], file)]
            cmdline += ['--reference-image', os.path.join(args.inverse[0], file.split(suffix[0])[0] + args.inverse[1])]

            cmdline += ['--transform', '[{},1]'.format(
                os.path.join(args.reg_dir[0], file_name + args.in_linear_intfix[0] + '0GenericAffine.mat'))]
            if args.in_deform_intfix is not None:
                cmdline += ['--transform', os.path.join(args.reg_dir[0], file_name + args.in_deform_intfix[0] + '1InverseWarp.nii.gz')]

        cmdline += ['--output', os.path.join(args.out_dir[0], file.split('.nii.gz')[0] + args.out_suffix[0])]


        #
        # launch

        print "Launching warping of file {}".format(file)

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = file.split('.nii.gz')[0]
        qsub_launcher.folder = args.out_dir[0]
        qsub_launcher.queue = 'short.q'
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]


# Wait for the jobs to finish (in cluster)
if is_hpc:
    print "Waiting for warping jobs to finish..."
    call(wait_jobs)

print "Warping finished."


