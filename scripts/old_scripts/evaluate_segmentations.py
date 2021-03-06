__author__ = 'gsanroma'

import argparse
from fnmatch import fnmatch
import os
import subprocess
import sys
import csv
from scheduler import Launcher, check_file_repeat
from shutil import rmtree

parser = argparse.ArgumentParser(description='Computes Dice score of estimated segmentations w.r.t. ground truth segmentations.\n'
                                             'Average per-label Dice score and average per-subject Dice score are stored in \n'
                                             'label_dice.csv and subj_dice.csv in est_dir directory, respectively')
parser.add_argument("--est_dir", type=str, nargs=1, action='append', required=True, help="Directory of estimated segmentations")
parser.add_argument("--est_suffix", type=str, nargs=1, required=True, help="Suffix of estimated segmentation files")
parser.add_argument("--gtr_dir", type=str, nargs=1, required=True, help="Directory of ground-truth segmentations")
parser.add_argument("--gtr_suffix", type=str, nargs=1, required=True, help="Suffix of ground truth segmentation files")

args = parser.parse_args()

if sys.platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

for est_dir in args.est_dir:

    #
    # Retrieve estimated files

    files_list = os.listdir(est_dir[0])
    est_files = [f for f in files_list if fnmatch(f, '*' + args.est_suffix[0])]
    est_names = [f.split(args.est_suffix[0])[0] for f in est_files]
    assert est_files, "No estimated segmentation found"

    #
    # Retrieve ground truth files

    gtr_files = [f + args.gtr_suffix[0] for f in est_names]
    assert not False in [os.path.exists(os.path.join(args.gtr_dir[0], f)) for f in gtr_files], "Some ground-truth segmentations not found"

    Nimg = len(est_files)

    # temp directory
    tmp_dir = os.path.join(est_dir[0], 'tmp')
    if os.path.exists(tmp_dir):
        rmtree(tmp_dir)
    os.makedirs(tmp_dir)

    imagemath_path = os.path.join(os.environ['ANTSPATH'],'ImageMath')

    wait_jobs = [os.path.join(os.environ['ANTSSCRIPTS'], "waitForSGEQJobs.pl"), '0', '10']

    out_paths = []

    for i_img in range(Nimg):

        est_path = os.path.join(est_dir[0], est_files[i_img])
        gtr_path = os.path.join(args.gtr_dir[0], gtr_files[i_img])
        out_path = os.path.join(tmp_dir, est_names[i_img])
        out_paths += [out_path]

        cmdline = "{} 3 {} DiceAndMinDistSum {} {}\n".format(imagemath_path, out_path, est_path, gtr_path)

        qsub_launcher = Launcher(cmdline)

        print "Launching Dice evaluation job for labels {}".format(est_names[i_img])

        qsub_launcher.name = est_names[i_img]
        qsub_launcher.folder = tmp_dir
        qsub_launcher.queue = 'short.q'
        job_id = qsub_launcher.run()

        if is_hpc:
            wait_jobs += [job_id]


    if is_hpc:
        print "Waiting for Dice evaluation jobs to finish..."
        subprocess.call(wait_jobs)
    print "Dice evaluation finished."

    subj_dices = dict([])
    label_dices = dict([])

    for out_path in out_paths:

        # Read per-label Dice
        check_file_repeat(out_path + '.csv')
        f = open(out_path + '.csv', 'r')
        reader = csv.reader(f)
        count = 0
        dice = 0.
        for row in reader:
            count += 1
            if count == 1:
                continue
            dice += float(row[1])
            try:
                label_dices[row[0].split('_')[1]] += float(row[1]) / len(out_paths)
            except:
                label_dices[row[0].split('_')[1]] = float(row[1]) / len(out_paths)

        f.close()

        subj_dices[os.path.basename(out_path)] = dice/(count-1)


    subj_dice_file = "subj_dice.csv"
    label_dice_file = "label_dice.csv"

    with open(os.path.join(est_dir[0], subj_dice_file), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, subj_dices.keys())
        writer.writeheader()
        writer.writerow(subj_dices)

    with open(os.path.join(est_dir[0], label_dice_file), 'w') as csvfile:
        writer = csv.DictWriter(csvfile, label_dices.keys())
        writer.writeheader()
        writer.writerow(label_dices)

    rmtree(tmp_dir)

