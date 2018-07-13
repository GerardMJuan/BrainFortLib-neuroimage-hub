"""
Sample images from a BIDS dataset.

This scripts samples a number of BIDS images and copies them onto a directory,
ready to be downloaded for visualization. The sampling is done randomly.
"""
from bids.grabbids import BIDSLayout
import argparse
import os
import numpy as np
from shutil import copyfile

# Sample execution
# python CODE/upf-nii/scripts/sample_directory.py --in_dir /homedtic/gmarti/DATA/Data/bids_test/derivatives/corrected/ --n_scans 5 --out_dir /homedtic/gmarti/DATA/Data/samples_reg/

parser = argparse.ArgumentParser(description='Registers images to a baseline. Can use initial transformation.')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='BIDS directory input images')
parser.add_argument("--n_scans", type=str, nargs=1, required=True, help='Number of n_scans')
parser.add_argument("--out_dir", type=str, nargs=1, required=True, help='output directory')

args = parser.parse_args()

# Check that bids directory is not empty
project_root = args.in_dir[0]
print(project_root)
layout = BIDSLayout(project_root)
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Check that out directory is not empty
out_dir = args.out_dir[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

files = layout.get(extensions='.nii.gz', modality='anat')
filenames = [f.filename for f in files]
# main loop
for f in np.random.choice(filenames, int(args.n_scans[0]), replace=False):
    # Copy image to new path
    img_path = f
    img_file = os.path.basename(img_path)
    copyfile(img_path, out_dir + img_file)
