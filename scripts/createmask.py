"""
Apply a mask to a set of MRI images.

Mask a set of MRI image with a target mask, with the possiblity of dilating
the mask.
"""

import argparse
from fnmatch import fnmatch
import os
import SimpleITK as sitk
import numpy as np
from scipy.ndimage.morphology import binary_dilation
import argparse

parser = argparse.ArgumentParser(description='Mask the MRI images')

parser.add_argument("--template_mask", type=str, nargs=1, help="Mask file")
parser.add_argument("--in_dir", type=str, nargs=1, help='directory of unmasked images')
parser.add_argument("--out_dir", type=str, nargs=1, help='directory where to store the images')
parser.add_argument("--img_suffix", type=str, nargs=1, help="suffix of the images")
parser.add_argument("--dilate", action="store_true", help="Dilate the mask.")
parser.add_argument("--size", type=int, nargs=1, default=[1], help="(optional) size of the dilation")

# Get input arguments
args = parser.parse_args()

# Get values
in_dir = args.in_dir[0]
directory_out = args.out_dir[0]
img_suffix = args.img_suffix[0]

# Create out directory if it doesnt exist
os.makedirs(directory_out, exist_ok=True)

# Read mask
template_sitk = sitk.ReadImage(args.template_mask[0])
templatemap = sitk.GetArrayFromImage(template_sitk)
img_size = template_sitk.GetSize()
mask = np.zeros(img_size, dtype=np.bool)
mask[templatemap > 0] = True

# If we want to dilate the mask:
if args.dilate:
    mask = binary_dilation(mask, iterations=int(args.size[0]))

mask_sitk = sitk.GetImageFromArray(mask.astype(np.uint8))
mask_sitk.CopyInformation(template_sitk)
# Final mask
mask = sitk.GetArrayFromImage(mask_sitk).astype(np.bool)

# Apply mask to all subjects
files_list = os.listdir(in_dir)
img_list = [f for f in sorted(files_list) if fnmatch(f, '*' + img_suffix)]

for img_file in img_list:
    img_name = img_file.split(img_suffix)[0]
    img_path = os.path.join(in_dir, img_file)

    # image
    img_sitk = sitk.ReadImage(os.path.join(in_dir, img_file))
    img = sitk.GetArrayFromImage(img_sitk)
    img[~mask] = img.min()
    aux = sitk.GetImageFromArray(img)
    aux.CopyInformation(img_sitk)
    print('Writing ' + img_name)
    sitk.WriteImage(aux, os.path.join(directory_out, img_file))
    del img_sitk, img, aux
