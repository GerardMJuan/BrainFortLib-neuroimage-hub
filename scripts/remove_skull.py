"""
Removes skull from a set of images using a corresponding
registered mask.
"""

from bids.grabbids import BIDSLayout
import argparse
from fnmatch import fnmatch
import os
import SimpleITK as sitk
import numpy as np
from sys import platform
from scipy.ndimage.morphology import binary_dilation

parser = argparse.ArgumentParser()
parser.add_argument("--base_dir", type=str, nargs=1, required=True, help="dir of input images")
parser.add_argument("--mask_name", type=str, nargs=1, required=True, help="dir of masks")
parser.add_argument("--img_name", type=str, nargs=1, required=True, help="output mask file")

parser.add_argument("--out_name", type=str, nargs=1, required=True, help="output mask file")
parser.add_argument("--dilation_radius", type=int, nargs=1, required=True, help="dilation radius")

args = parser.parse_args()

if platform == 'darwin':
    is_hpc = False
else:
    is_hpc = True

# Check that bids directory is not empty
project_root = args.base_dir[0] + 'derivatives/' + args.img_name[0]
layout_mri = BIDSLayout(project_root)

project_root = args.base_dir[0] + 'derivatives/'  + args.mask_name[0]
layout_masks = BIDSLayout(project_root)

# Create img list
files = layout_mri.get(extensions='.nii.gz', modality='anat')

assert len(layout_mri.get_subjects()) > 0, "No subjects in directory!"
assert len(layout_masks.get_subjects()) > 0, "No masks in directory!"

out_dir = args.base_dir[0] + 'derivatives/' + args.out_name[0]
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

for img in files:
    img_path = img.filename
    img_file = os.path.basename(img_path)

    # Find and read masks
    mask = layout_masks.get(subject=img.subject, session=img.session, modality=img.modality)
    mask = mask[0].filename
    template_sitk = sitk.ReadImage(mask)
    template_array = sitk.GetArrayFromImage(template_sitk)

    # Create and dilate mask
    img_size = template_sitk.GetSize()
    mask = np.zeros(img_size[::-1], dtype=np.bool)
    mask[template_array > 0.2] = True
    struct = np.ones((args.dilation_radius[0],)*3, dtype=np.bool)
    mask = binary_dilation(mask, struct)

    # Read image
    img_sitk = sitk.ReadImage(img_path)
    img_array = sitk.GetArrayFromImage(img_sitk)

    # Apply mask
    print(img_array.shape)
    print(mask.shape)
    img_array[~mask] = 0
    img_sitk_cropped = sitk.GetImageFromArray(img_array)
    img_sitk_cropped.CopyInformation(img_sitk)
    # Output to file
    out_dir_img = out_dir + img.subject + '/' + img.session + '/' + img.modality + '/'
    if not os.path.exists(out_dir_img):
        os.makedirs(out_dir_img)
""""
    sitk.WriteImage(img_sitk_cropped, out_dir_img + img_file)
