import argparse
from fnmatch import fnmatch
from scheduler import Launcher
from sys import platform
from subprocess import call
import os
import SimpleITK as sitk
import numpy as np
from shutil import copyfile

parser = argparse.ArgumentParser(description='Processes the images including N4 correction and histogram matching to template.\n'
                                             'Optionally, images and/or template can be masked out (e.g., remove skull) given the mask file.')

parser.add_argument("--in_dir",type=str, nargs=1, required=True, help='directory with the input images')
parser.add_argument("--in_metadata",type=str, nargs=1, required=True, help='metadata')
parser.add_argument("--img_suffix",type=str, nargs=1, required=True, help='suffix of the image files')
parser.add_argument("--maskout_suffix", type=str, nargs=1, help="suffix mask files in case want to maskout subjects")
parser.add_argument("--label_suffix", type=str, nargs=1, help="transfer label files to the output directory")
parser.add_argument("--n4", action="store_true", help="N4 bias correction")
parser.add_argument("--denoising", action="store_true", help="Denoising")
parser.add_argument("--histmatch", action="store_true", help="histogram matching (needs template)")
parser.add_argument("--template_file", type=str, nargs=1, help="template image")
parser.add_argument("--template_maskout_mask", type=str, nargs=1, help="maskout template")
parser.add_argument("--template_norm", action="store_true", help="normalize template intensities between [0..1]")
parser.add_argument("--out_dir_baseline", type=str, nargs=1, help='directory to store processed images (baselines)')
parser.add_argument("--out_dir_followups", type=str, nargs=1, help='directory to store processed images (followups)')


args = parser.parse_args()


if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True


# One of the arguments must be a directory with all the baselines, such that is easy to, given a followup, we can perform in a loop all the registrations with the correct 

os.environ["ANTSPATH"] = "/homedtic/gsanroma/CODE/LIB/ANTs/build/bin"

os.environ["ANTSSCRIPTS"] = "/homedtic/gsanroma/CODE/LIB/ANTs/Scripts"

n_jobs = 0
n_total_jobs = 80

# python3 process_images_fromfile.py --in_dir /homedtic/gmarti/DATA/Data/ --in_metadata /homedtic/gmarti/DATA/Data/
#
# Initial checks
#

if not args.histmatch:
    assert args.template_file is None and args.template_maskout_mask is None and not args.template_norm, "Unnecessary template if not histmatch"

if args.histmatch:
    assert args.template_file is not None, "Need template for histogram matching"

if args.template_file is not None:
    assert os.path.exists(args.template_file[0]), "Template file not found"

if args.template_maskout_mask is not None:
    assert os.path.exists(args.template_maskout_mask[0]), "Template mask not found"

if args.in_metadata is not None:
    assert os.path.exists(args.in_metadata[0]), "Metadata file not found"

# input directory
in_metadata = args.in_metadata[0]
with open(in_metadata) as f:
    content = f.readlines()
    lines = [line.rstrip('\n').split(',') for line in content]
    files_list = [line[12].rstrip('\r') for line in lines]                     # list of paths of images
    img_list = [f for f in files_list if fnmatch(f, '*' + args.img_suffix[0])]
    baseline_list = [line[10] for line in lines]                # if 0, that image is a baseline. If not, followup

assert img_list, "List of input images is empty"

if args.maskout_suffix is not None:
    mask_list = [f.split(args.img_suffix[0])[0] + args.maskout_suffix[0] for f in img_list]
    assert False not in [os.path.exists(os.path.join(args.in_dir[0], f)) for f in mask_list]

if args.label_suffix is not None:
    # print "label suffix {}".format(args.label_suffix[0])
    label_list = [f.split(args.img_suffix[0])[0] + args.label_suffix[0] for f in img_list]
    # a = [os.path.exists(os.path.join(args.in_dir[0], f)) for f in label_list]
    # b = [f for i, f in enumerate(label_list) if not a[i]]
    # print b
    assert False not in [os.path.exists(os.path.join(args.in_dir[0], f)) for f in label_list]

# create output directories
if not os.path.exists(args.out_dir_baseline[0]):
    os.makedirs(args.out_dir_baseline[0])

if not os.path.exists(args.out_dir_followups[0]):
    os.makedirs(args.out_dir_followups[0])

in_dir = args.in_dir[0]
#
# Pipeline
#

if args.maskout_suffix is not None:

    lab_list = []
    if args.label_suffix is not None:
        lab_list = label_list

    for img_file, lab_file, mask_file in map(None, img_list, lab_list, mask_list):

        print("Masking out subject %s" % img_file.split(args.img_suffix[0])[0])

        # mask
        mask_sitk = sitk.ReadImage(os.path.join(in_dir, mask_file))
        mask = sitk.GetArrayFromImage(mask_sitk).astype(np.bool)
        copyfile(os.path.join(in_dir, mask_file), os.path.join(args.out_dir[0], mask_file))

        # image
        img_sitk = sitk.ReadImage(os.path.join(args.in_dir[0], img_file))
        img = sitk.GetArrayFromImage(img_sitk)
        img[~mask] = img.min()
        aux = sitk.GetImageFromArray(img)
        aux.CopyInformation(img_sitk)
        sitk.WriteImage(aux, os.path.join(args.out_dir[0], img_file))

        # label
        if lab_file:
            lab_sitk = sitk.ReadImage(os.path.join(args.in_dir[0], lab_file))
            lab = sitk.GetArrayFromImage(lab_sitk)
            lab[~mask] = lab.min()
            aux = sitk.GetImageFromArray(lab)
            aux.CopyInformation(lab_sitk)
            sitk.WriteImage(aux, os.path.join(args.out_dir[0], lab_file))

    # assign input directory for subsequent steps
    in_dir = args.out_dir[0]

elif args.label_suffix is not None:

    for lab_file in label_list:
        copyfile(os.path.join(in_dir, lab_file), os.path.join(args.out_dir[0], lab_file))


if args.n4:
    '''
    n4_path = os.path.join(os.environ['ANTSPATH'], 'N4BiasFieldCorrection')
    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']

    for (img_file,baseline) in zip(img_list,baseline_list):

        cmdline = [n4_path, '--image-dimensionality', '3']
        cmdline += ['--input-image', os.path.join(in_dir, img_file)]
        cmdline += ['--shrink-factor', '3']
        cmdline += ['--convergence', '50x50x30x20', '1e-6']
        cmdline += ['--bspline-fitting', '300']
        if (baseline == '0'):
            cmdline += ['--output', os.path.join(args.out_dir_baseline[0], img_file)]
        else:
            cmdline += ['--output', os.path.join(args.out_dir_followups[0], img_file)]

        print "Launching N4 for {}".format(img_file)

        qsub_launcher = Launcher(' '.join(cmdline))
        
        qsub_launcher.name = os.path.splitext(os.path.basename(img_file))[0]

        if (baseline == '0'):
            qsub_launcher.folder = args.out_dir_baseline[0]
        else:
            qsub_launcher.folder = args.out_dir_followups[0]

        qsub_launcher.queue = 'short.q'
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]
        
        n_jobs += 1
        
        if is_hpc and n_total_jobs <= n_jobs:
            print "Waiting for N4 jobs to finish..."
            call(wait_jobs)

            # Put njobs and waitjobs at 0 again
            n_jobs = 0
            wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']


    # Wait for the jobs to finish (in cluster)
    if is_hpc:
        n_jobs = 0
        print "Waiting for N4 jobs to finish..."
        call(wait_jobs)

    print "N4 finished."
    '''
    # assign input directory for subsequent steps


'''
if args.denoising:

    denoise_path = os.path.join(os.environ['ANTSPATH'], 'DenoiseImage')
    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']

    for (img_file,baseline) in zip(img_list[2892:],baseline_list[2892:]):
        img_file = os.path.basename(img_file)
        if (baseline == '0'):
            in_dir = args.out_dir_baseline[0]
        else:
            in_dir = args.out_dir_followups[0]
        cmdline = [denoise_path, '--image-dimensionality', '3']
        cmdline.extend(['--input-image', os.path.join(in_dir, img_file)])
        
        cmdline.extend(['--noise-model', 'Rician'])


        if (baseline == '0'):
            cmdline += ['--output', os.path.join(args.out_dir_baseline[0], img_file)]
        else:
            cmdline += ['--output', os.path.join(args.out_dir_followups[0], img_file)]

        print "Launching Denoising for {}".format(img_file)

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = img_file
        if (baseline == '0'):
            qsub_launcher.folder = args.out_dir_baseline[0]
        else:
            qsub_launcher.folder = args.out_dir_followups[0]
        qsub_launcher.queue = 'short.q'
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]
        
        n_jobs += 1
        
        if is_hpc and n_total_jobs <= n_jobs:
            print "Waiting for Denoising jobs to finish..."
            call(wait_jobs)

            # Put njobs and waitjobs at 0 again
            n_jobs = 0
            wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']


    # Wait for the jobs to finish (in cluster)
    if is_hpc:
        n_jobs = 0
        print "Waiting for Denoising jobs to finish..."
        call(wait_jobs)

    print "Denoising finished."

    # assign input directory for subsequent steps
    if (baseline == '0'):
        in_dir = args.out_dir_baseline[0]
    else:
        in_dir = args.out_dir_followups[0]
'''

if args.histmatch:

    #
    # process template

    if args.template_maskout_mask is not None or args.template_norm:

        print("Processing template")

        template_sitk = sitk.ReadImage(args.template_file[0])
        template = sitk.GetArrayFromImage(template_sitk)

        # mask out template file
        if args.template_maskout_mask is not None:
            mask_sitk = sitk.ReadImage(args.template_maskout_mask[0])
            mask = sitk.GetArrayFromImage(mask_sitk).astype(np.bool)
            template[~mask] = template.min()
            copyfile(args.template_maskout_mask[0], os.path.join(args.out_dir_baseline[0], os.path.basename(args.template_maskout_mask[0])))

        if args.template_norm:
            template = (template - template.min()) / (template.max() - template.min())

        aux = sitk.GetImageFromArray(template)
        aux.CopyInformation(template_sitk)
        sitk.WriteImage(aux, os.path.join(args.out_dir_baseline[0], os.path.basename(args.template_file[0])))

    else:
        copyfile(args.template_file[0], os.path.join(args.out_dir_baseline[0], os.path.basename(args.template_file[0])))

    imagemath_path = os.path.join(os.environ['ANTSPATH'],'ImageMath')
    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    for (img_file,baseline) in zip(img_list[2071:],baseline_list[2071:]):
        img_file = os.path.basename(img_file)

        if (baseline == '0'):
            in_file = os.path.join(args.out_dir_baseline[0], img_file)
            out_file = os.path.join(args.out_dir_baseline[0], img_file)
        else:
            in_file = os.path.join(args.out_dir_followups[0], img_file)
            out_file = os.path.join(args.out_dir_followups[0], img_file)
        
        cmdline = [imagemath_path, '3', out_file, 'TruncateImageIntensity', in_file, '0.05', '0.95']

        print("Launching histogram truncate of {}".format(img_file))

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = img_file
        if (baseline == '0'):
            qsub_launcher.folder = args.out_dir_baseline[0]
        else:
            qsub_launcher.folder = args.out_dir_followups[0]
        qsub_launcher.queue = 'short.q'
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]
        
        n_jobs += 1

        if is_hpc and n_total_jobs <= n_jobs:
            print("Waiting for histogram matching jobs to finish...")
            call(wait_jobs)

            # Put njobs and waitjobs at 0 again
            n_jobs = 0
            wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    print('Finished truncating')
    for (img_file,baseline) in zip(img_list,baseline_list):
        img_file = os.path.basename(img_file)

        if (baseline == '0'):
            in_file = os.path.join(args.out_dir_baseline[0], img_file)
            out_file = os.path.join(args.out_dir_baseline[0], img_file)
            tpl_file = os.path.join(args.out_dir_baseline[0], os.path.basename(args.template_file[0]))
        else:
            in_file = os.path.join(args.out_dir_followups[0], img_file)
            out_file = os.path.join(args.out_dir_followups[0], img_file)
            tpl_file = os.path.join(args.out_dir_followups[0], os.path.basename(args.template_file[0]))

        cmdline = [imagemath_path, '3', out_file, 'HistogramMatch', in_file, tpl_file]

        print("Launching histogram match of {}".format(img_file))

        qsub_launcher = Launcher(' '.join(cmdline))
        qsub_launcher.name = img_file
        if (baseline == '0'):
            qsub_launcher.folder = args.out_dir_baseline[0]
        else:
            qsub_launcher.folder = args.out_dir_followups[0]
        qsub_launcher.queue = 'short.q'
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]
        
        n_jobs += 1
        
        if is_hpc and n_total_jobs <= n_jobs:
            print("Waiting for histogram matching jobs to finish...")
            call(wait_jobs)

            # Put njobs and waitjobs at 0 again
            n_jobs = 0
            wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']


    # Wait for the jobs to finish (in cluster)
    if is_hpc:
        n_jobs = 0
        print("Waiting for histogram matching jobs to finish...")
        call(wait_jobs)

    print("Histogram matching finished.")




