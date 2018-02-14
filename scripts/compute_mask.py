import argparse
from fnmatch import fnmatch
import os
import SimpleITK as sitk
import numpy as np
from scipy.ndimage.morphology import binary_dilation

parser = argparse.ArgumentParser()
parser.add_argument("--labels_dir", type=str, nargs=1, required=True, help="dir of labelmaps")
parser.add_argument("--labels_suffix", type=str, nargs=1, required=True, help="suffix for labelmaps")
parser.add_argument("--template_file", type=str, nargs=1, required=True, help="template file")
parser.add_argument("--output_mask", type=str, nargs=1, required=True, help="output mask file")
parser.add_argument("--dilation_radius", type=int, nargs=1, required=True, help="dilation radius")

args = parser.parse_args()
# args = parser.parse_args('--labels_dir /Users/gsanroma/DATA/DATABASES/ADNI/atlases/ensemble_data/35atlases_cmn --labels_suffix _lab.nii.gz --template_file /Users/gsanroma/DATA/DATABASES/ADNI/atlases/processed/template.nii.gz --output_mask /Users/gsanroma/DATA/DATABASES/ADNI/atlases/ensemble_data/mask35.nii.gz --dilation_radius 5'.split())


files_list = os.listdir(args.labels_dir[0])
label_files_list = [f for f in files_list if fnmatch(f, '*' + args.labels_suffix[0])]
assert label_files_list, "List of target labelmaps is empty"

template_sitk = sitk.ReadImage(args.template_file[0])
img_size = template_sitk.GetSize()

mask = np.zeros(img_size, dtype=np.bool)

for label_file in label_files_list:

    print 'reading {}'.format(label_file)

    labelmap_sitk = sitk.ReadImage(os.path.join(args.labels_dir[0], label_file))
    labelmap = sitk.GetArrayFromImage(labelmap_sitk)

    mask[labelmap > 0] = True

struct = np.ones((args.dilation_radius[0],)*3, dtype=np.bool)
mask = binary_dilation(mask, struct)

mask_sitk = sitk.GetImageFromArray(mask.astype(np.uint8))
mask_sitk.CopyInformation(template_sitk)

sitk.WriteImage(mask_sitk, args.output_mask[0])