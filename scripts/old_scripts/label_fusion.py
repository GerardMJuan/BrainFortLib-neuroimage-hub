
import os
import argparse
from fnmatch import fnmatch
from pickle import load
import numpy as np
from subprocess import call
from scheduler import Launcher
from sys import platform
from shutil import rmtree
import pblf_py

parser = argparse.ArgumentParser(description='Segments target images with Joint label fusion.\n'
                                             'Atlas parameters are optional. In not given, then leave-one-out\n'
                                             'label fusion is done among target images (target labels must be given).\n'
                                             'Patch size and search radius can be specified (otherwise 2x2x2, 3x3x3 are used, respect.)')
parser.add_argument("--target_dir", type=str, nargs=1, required=True, help='directory of target images')
parser.add_argument("--target_img_suffix", type=str, nargs=1, required=True, help='image suffixes')
parser.add_argument("--target_lab_suffix", type=str, nargs=1, help="(optional) in case leave-one-out label fusion")
parser.add_argument("--target_reg_dir", type=str, nargs=1, required=True, help='directory with target transformations to template space')
parser.add_argument("--target_linear_intfix", type=str, nargs=1, required=True, help="intfix of the input linear transform")
parser.add_argument("--target_deform_intfix", type=str, nargs=1, help="(optional) intfix of the input deformation field")
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='directory to store label fusion results')
parser.add_argument("--out_suffix", type=str, nargs=1, required=True, help="suffix to be added to the target image name without target_img_suffix")
parser.add_argument("--tmp_dir", type=str, nargs=1, required=True, help='temp directory')

parser.add_argument("--atlas_dir", type=str, nargs=1)
parser.add_argument("--atlas_img_suffix", type=str, nargs=1)
parser.add_argument("--atlas_lab_suffix", type=str, nargs=1)
parser.add_argument("--atlas_reg_dir", type=str, nargs=1)
parser.add_argument("--atlas_linear_intfix", type=str, nargs=1)
parser.add_argument("--atlas_deform_intfix", type=str, nargs=1)

parser.add_argument("--template_file", type=str, nargs=1, help="(optional) do label fusion in template space")
parser.add_argument("--atlas_selection", type=str, nargs=4, help="(optional) number of atlases, scores file, suffix inside scores file for target, idem for atlas")
parser.add_argument("--keep_tmp", action="store_true", help='keep temp directory (for debug)')
parser.add_argument("--concurrent", action="store_true", help="concurrent label fusion (faster but takes more disk space) (use only when small number of atlases)")
parser.add_argument("--probabilities", action="store_true", help="compute segmentation probabilities")
parser.add_argument("--method", type=str, nargs='+', action='append', help="(optional) suffix to out_dir, [Joint|nlwv], [ patch_rad,search_rad | h,patch_rad,search_rad,fusion_rad,struct_sim,norm ]")

args = parser.parse_args()
# args = parser.parse_args('--target_dir /Users/gsanroma/DATA/DATABASES/ADNI/atlases/data_processed --target_img_suffix _brain.nii.gz --target_lab_suffix _labels.nii.gz --target_reg_dir /Users/gsanroma/DATA/DATABASES/ADNI/atlases/transforms --target_linear_intfix _mA4Xtpl --out_dir kk --tmp_dir /Users/gsanroma/DATA/DATABASES/ADNI/atlases/tmp --atlas_selection 35 /Users/gsanroma/DATA/DATABASES/ADNI/atlases/NormCorr_A4.dat _brainWarped.nii.gz'.split())

#
# PATHS
#

code_dir = os.path.join(os.environ['HOME'], 'CODE')
python_path = os.path.join(os.environ['HOME'], 'anaconda', 'envs', 'sitkpy', 'bin', 'python')
warptotemplate_path = os.path.join(code_dir, 'scripts_py', 'warp_to_template.py')
warpatlasestotarget_path = os.path.join(code_dir, 'scripts_py', 'warp_atlases_to_target.py')

#
# Label Fusion function
#

def label_fusion(target_path, atlas_img_path_list, atlas_lab_path_list, out_file, probabilities, params_list):

    out_dir = os.path.dirname(out_file)
    out_name = os.path.basename(out_file).split(os.extsep, 1)[0]

    if params_list[0] == 'Joint':

        jointfusion_path = os.path.join(os.environ['ANTSPATH'], 'jointfusion')

        prob_dir =  os.path.join(out_dir, out_name)
        prob_path = os.path.join(prob_dir, 'prob%d.nii.gz')

        cmdline = [jointfusion_path, '3', '1']
        cmdline += ['-g'] + atlas_img_path_list
        cmdline += ['-tg', target_path]
        cmdline += ['-l'] + atlas_lab_path_list
        cmdline += ['-m', 'Joint']
        cmdline += [item for sublist in zip(['-rp', '-rs'], params_list[1:]) for item in sublist]
        if probabilities:
            os.makedirs(prob_dir)
            cmdline += ['-p', prob_path]
        cmdline += [out_file]

    else:

        python_path = os.path.join(os.environ['HOME'], 'anaconda', 'envs', 'sitkpy', 'bin', 'python')
        mod_path = os.path.join(os.environ['HOME'], 'CODE', 'mod_py')
        nlwv_path = os.path.join(mod_path, 'pblf_py.py')

        cmdline = [python_path, '-u', nlwv_path]

        cmdline += ['--atlas_img_list'] + atlas_img_path_list
        cmdline += ['--target_img', target_path]
        cmdline += ['--atlas_lab_list'] + atlas_lab_path_list
        cmdline += ['--method'] + params_list[:2]
        cmdline += [item for sublist in zip(['--patch_radius', '--search_radius', '--fusion_radius', '--struct_sim', '--normalization',], params_list[2:]) for item in sublist]
        if probabilities:
            cmdline += ['--probabilities']
        cmdline += ['--out_file', out_file]

    # launch
    qsub_launcher = Launcher(' '.join(cmdline))
    qsub_launcher.name = "{}_joint".format(out_name)
    qsub_launcher.folder = out_dir
    # qsub_launcher.queue = 'short.q'
    qsub_launcher.queue = 'default.q'

    return qsub_launcher.run()


#
# Main program
#

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

files_list = os.listdir(args.target_dir[0])
target_img_files = [f for f in files_list if fnmatch(f, '*' + args.target_img_suffix[0])]
assert target_img_files, "List of target files is empty"
Ntar = len(target_img_files)

if args.target_lab_suffix is not None:
    target_lab_files = [f.split(args.target_img_suffix[0])[0] + args.target_lab_suffix[0] for f in target_img_files]
    assert False not in [os.path.exists(os.path.join(args.target_dir[0], f)) for f in target_lab_files], "Some target label file not found"

is_loo = False
if args.atlas_dir is not None:
    files_list = os.listdir(args.atlas_dir[0])
    atlas_img_files = [f for f in files_list if fnmatch(f, '*' + args.atlas_img_suffix[0])]
    assert atlas_img_files, "List of atlas files is empty"
    atlas_lab_files = [f.split(args.atlas_img_suffix[0])[0] + args.atlas_lab_suffix[0] for f in atlas_img_files]
    assert False not in [os.path.exists(os.path.join(args.atlas_dir[0], f)) for f in atlas_lab_files], "Some target label file not found"
    Natl = len(atlas_img_files)
    atlas_dir = args.atlas_dir[0]
    atlas_img_suffix = args.atlas_img_suffix[0]
    atlas_lab_suffix = args.atlas_lab_suffix[0]
    atlas_reg_dir = args.atlas_reg_dir[0]
    atlas_linear_intfix = args.atlas_linear_intfix[0]
    if args.atlas_deform_intfix is not None:
        atlas_deform_intfix = args.atlas_deform_intfix[0]
else:
    print "Leave one out segmentation"
    is_loo = True
    atlas_img_files = target_img_files
    atlas_lab_files = target_lab_files
    Natl = Ntar
    atlas_dir = args.target_dir[0]
    atlas_img_suffix = args.target_img_suffix[0]
    atlas_lab_suffix = args.target_lab_suffix[0]
    atlas_reg_dir = args.target_reg_dir[0]
    atlas_linear_intfix = args.target_linear_intfix[0]
    if args.target_deform_intfix is not None:
        atlas_deform_intfix = args.target_deform_intfix[0]

if not os.path.exists(args.tmp_dir[0]):
    os.makedirs(args.tmp_dir[0])

#
# Atlas selection
#

if args.atlas_selection is not None:

    print "Reading scores for atlas selection"

    # load scores file
    f = open(args.atlas_selection[1], 'r')
    in_dir, in_files_list, in2_dir, in2_files_list, scores_aux = load(f)
    f.close()

    target_names = [f.split(args.target_img_suffix[0])[0] for f in target_img_files]
    s_target_names = [f.split(args.atlas_selection[2])[0] for f in in_files_list]
    atlas_names = target_names
    if not is_loo:
        atlas_names = [f.split(args.atlas_img_suffix[0])[0] for f in atlas_img_files]
    s_atlas_names = [f.split(args.atlas_selection[3])[0] for f in in2_files_list]

    assert set(s_target_names) == set(target_names), "Filenames of scores file do not match"
    if not is_loo:
        assert set(s_atlas_names) == set(atlas_names), "Filenames of scores file do not match"
    scores = np.zeros((Ntar, Natl), dtype=np.float32)

    for i_t in range(Ntar):
        i2_t = [i for i, f in enumerate(s_target_names) if target_names[i_t] == f][0]
        for i_a in range(Natl):
            if is_loo and target_names[i_t] == atlas_names[i_a]:
                continue
            i2_a = [i for i, f in enumerate(s_atlas_names) if atlas_names[i_a] == f][0]
            scores[i_t, i_a] = scores_aux[i2_t, i2_a]

    atlas_idx = np.argsort(scores, axis=1)[:, :-int(args.atlas_selection[0])-1:-1]

else:

    print "No atlas selection"

    if is_loo:
        atlas_idx = np.array([list(set(range(Ntar))-{i}) for i in range(Ntar)])
    else:
        atlas_idx = np.array([range(Natl),] * Ntar)


#
# Label Fusion
#

# Label fusion in template space
if args.template_file is not None:

    cmdline = [python_path, '-u', warptotemplate_path]
    cmdline += ['--in_dir', args.target_dir[0]]
    cmdline += ['--linear_suffix', args.target_img_suffix[0]]
    if args.target_lab_suffix is not None:
        cmdline += ['--nearest_suffix', args.target_lab_suffix[0]]
    cmdline += ['--template_file', args.template_file[0]]
    cmdline += ['--reg_dir', args.target_reg_dir[0]]
    cmdline += ['--in_linear_intfix', args.target_linear_intfix[0]]
    if args.target_deform_intfix is not None:
        cmdline += ['--in_deform_intfix', args.target_deform_intfix[0]]
    cmdline += ['--out_dir', args.tmp_dir[0]]
    cmdline += ['--out_suffix', 'Warped.nii.gz']
    cmdline += ['--float']

    print "Warping targets to template"

    call(cmdline)

    if not is_loo:

        cmdline = [python_path, '-u', warptotemplate_path]
        cmdline += ['--in_dir', args.atlas_dir[0]]
        cmdline += ['--linear_suffix', args.atlas_img_suffix[0]]
        cmdline += ['--nearest_suffix', args.atlas_lab_suffix[0]]
        cmdline += ['--template_file', args.template_file[0]]
        cmdline += ['--reg_dir', args.atlas_reg_dir[0]]
        cmdline += ['--in_linear_intfix', args.atlas_linear_intfix[0]]
        if args.atlas_deform_intfix is not None:
            cmdline += ['--in_deform_intfix', args.atlas_deform_intfix[0]]
        cmdline += ['--out_dir', args.tmp_dir[0]]
        cmdline += ['--out_suffix', 'Warped.nii.gz']
        cmdline += ['--float']

        print "Warping atlases to template"

        call(cmdline)


wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '60']

for i_t in range(Ntar):

    target_name = target_img_files[i_t].split(args.target_img_suffix[0])[0]

    # Label fusion in target space
    if args.template_file is None:

        target_tmp_dir = os.path.join(args.tmp_dir[0], target_name)

        os.makedirs(target_tmp_dir)

        for i_a in atlas_idx[i_t]:
            os.symlink(os.path.join(atlas_dir, atlas_img_files[i_a]), os.path.join(target_tmp_dir, atlas_img_files[i_a]))
            os.symlink(os.path.join(atlas_dir, atlas_lab_files[i_a]), os.path.join(target_tmp_dir, atlas_lab_files[i_a]))

        cmdline = [python_path, '-u', warpatlasestotarget_path]
        cmdline += ['--atlas_dir', target_tmp_dir]
        cmdline += ['--atlas_linear_suffix', atlas_img_suffix]
        cmdline += ['--atlas_nearest_suffix', atlas_lab_suffix]
        cmdline += ['--atlas_reg_dir', atlas_reg_dir]
        cmdline += ['--atlas_linear_intfix', atlas_linear_intfix]
        try:
            cmdline += ['--atlas_deform_intfix', atlas_deform_intfix]
        except:
            pass
        cmdline += ['--target_file', os.path.join(args.target_dir[0], target_img_files[i_t])]
        cmdline += ['--target_suffix', args.target_img_suffix[0]]
        cmdline += ['--target_reg_dir', args.target_reg_dir[0]]
        cmdline += ['--target_linear_intfix', args.target_linear_intfix[0]]
        if args.target_deform_intfix is not None:
            cmdline += ['--target_deform_intfix', args.target_deform_intfix[0]]
        cmdline += ['--out_dir', target_tmp_dir]
        cmdline += ['--out_suffix', 'Warped.nii.gz']
        cmdline += ['--float']

        print "Warping atlases to target {}".format(target_img_files[i_t])

        call(cmdline)

        target_path = os.path.join(args.target_dir[0], target_img_files[i_t])
        atlas_img_path_list = [os.path.join(target_tmp_dir, atlas_img_files[i_a].split(os.extsep, 1)[0] + 'Warped.nii.gz') for i_a in atlas_idx[i_t]]
        atlas_lab_path_list = [os.path.join(target_tmp_dir, atlas_lab_files[i_a].split(os.extsep, 1)[0] + 'Warped.nii.gz') for i_a in atlas_idx[i_t]]

    else:

        target_path = os.path.join(args.tmp_dir[0], target_img_files[i_t].split(os.extsep, 1)[0] + 'Warped.nii.gz')
        atlas_img_path_list = [os.path.join(args.tmp_dir[0], atlas_img_files[i_a].split(os.extsep, 1)[0] + 'Warped.nii.gz') for i_a in atlas_idx[i_t]]
        atlas_lab_path_list = [os.path.join(args.tmp_dir[0], atlas_lab_files[i_a].split(os.extsep, 1)[0] + 'Warped.nii.gz') for i_a in atlas_idx[i_t]]

    #
    # Label fusion

    print "Launching label fusion of file {}".format(target_img_files[i_t])

    params_superlist = [['', 'Joint', '2x2x2', '3x3x3']]
    if args.method is not None:
        params_superlist = args.method

    jobs_list = []
    for params_list in params_superlist:

        out_dir = args.out_dir[0] + params_list[0]

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        out_file = os.path.join(out_dir, target_name + args.out_suffix[0])

        job_id = label_fusion(target_path, atlas_img_path_list, atlas_lab_path_list, out_file, args.probabilities, params_list[1:])

        if is_hpc:
            jobs_list += [job_id]

    if is_hpc:
        if args.concurrent:
            wait_jobs += jobs_list
        else:
            call(wait_jobs + jobs_list)

    # Remove warped files
    if not args.keep_tmp and not args.concurrent and args.template_file is None:
        rmtree(target_tmp_dir)


# Wait for the jobs to finish (in cluster)
if is_hpc and args.concurrent:
    print "Waiting for label fusion jobs to finish..."
    call(wait_jobs)

print "Label fusion finished."

if not args.keep_tmp:
    rmtree(args.tmp_dir[0])





