"""
Script to visualize slices from a dataset of MRI images.

This script is used for easy and quick checking of .nii 3D images. It saves to disk several png images
of determined slices of the image. Position of slices can be determined. Input directory should be a BIDS
directory.
"""

from bids.grabbids import BIDSLayout
import os
import argparse
from fnmatch import fnmatch
from sys import platform
from subprocess import call
from matplotlib import pyplot as plt
import SimpleITK as sitk
from dltk.io.augmentation import *
from dltk.io.preprocessing import *

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir",type=str,nargs=1, required=True, help="dir of images (should be BIDS)")
parser.add_argument("--in_suffix",type=str,nargs=1, required=True, help="valid suffix for brain images")
parser.add_argument("--out_dir",type=str,nargs=1, required=True, help="output directory of images")
parser.add_argument("--slices",type=str,nargs=1, required=False,  help="(optional) list of slices (separate by commas)")

# Test of execution
# python /homedtic/gmarti/CODE/upf-nii/scripts/utils/visualize_slices.py --input_dir /homedtic/gmarti/DATA/Data/ADNI_BIDS/derivatives/noskull --in_suffix .nii.gz --out_dir  /homedtic/gmarti/DATA/Data/png_samples/

#TODO add perspective to print. Per default, it prints it by
args = parser.parse_args()
# If the slices are not specified, the program will just print a slide in the middle.

# Check that bids directory is not empty(TODO)
project_root = args.input_dir[0]
print(project_root)
layout = BIDSLayout(project_root)
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Create img list
files = layout.get(extensions = args.in_suffix[0], modality = 'anat')

# create output directory
# output directory is of the form:
out_dir = args.out_dir[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Main loop

for img in files:
    img_path = img.filename
    img_file = os.path.basename(img_path)
    img_name = img_file.split(args.in_suffix[0])[0]

    # Load the image
    sitk_t1 = sitk.ReadImage(img_path)
    t1 = sitk.GetArrayFromImage(sitk_t1)

    # Normalise the image to zero mean/unit std dev:
    t1 = whitening(t1)

    # Create a 4D Tensor with a dummy dimension for channels
    t1 = t1[..., np.newaxis]

    # Depending on i fwe have set an slice or not
    if args.slices:
        print('NYI')
        # TODO
    else:
        # Save it to disk
        sl = t1.shape[0]//2
        img_final = np.squeeze(t1[sl, :, :])
        name_img = img.subject + '_' + img.session + '_' + str(sl) + '1_nosk.png'
        plt.imsave(out_dir + name_img, img_final, cmap='gray')

        # Save it to disk
        sl = t1.shape[1]//2
        img_final = np.squeeze(t1[:, sl, :])
        name_img = img.subject + '_' + img.session + '_' + str(sl) + '2_nosk.png'
        plt.imsave(out_dir + name_img, img_final, cmap='gray')

        # Save it to disk
        sl = t1.shape[2]//2
        img_final = np.squeeze(t1[:, :, sl])
        name_img = img.subject + '_' + img.session + '_' + str(sl) + '3_nosk.png'
        plt.imsave(out_dir + name_img, img_final, cmap='gray')
