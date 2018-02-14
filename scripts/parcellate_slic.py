__author__ = 'gsanroma'

import SimpleITK as sitk
import numpy as np
import argparse
import os
from skimage.segmentation import slic

parser = argparse.ArgumentParser()
parser.add_argument("segments",type=int)
parser.add_argument("compactness",type=int)
parser.add_argument("data_dir",type=str)
parser.add_argument("template_img",type=str)
parser.add_argument("template_mask",type=str)
parser.add_argument("parcel_file",type=str)

args = parser.parse_args()
# args = parser.parse_args(['29000','100','/Users/gsanroma/DATA/stacking/NeoMater/parcellations','mask_d5.nii.gz','mask_d5.nii.gz','/Users/gsanroma/DATA/stacking/NeoMater/parcellations/parcel.nii.gz'])


template_img = os.path.join(args.data_dir, args.template_img)
template_mask = os.path.join(args.data_dir, args.template_mask)

template_sitk = sitk.ReadImage(template_img)
template = sitk.GetArrayFromImage(template_sitk).astype(np.float64)

mask_sitk = sitk.ReadImage(template_mask)
mask = sitk.GetArrayFromImage(mask_sitk).astype(np.bool)

if args.segments > 1:

    template[~mask] = 1e30#np.finfo(np.float64).max/2.#np.inf#

    r = np.any(mask, axis=(1, 2))
    c = np.any(mask, axis=(0, 2))
    z = np.any(mask, axis=(0, 1))

    min0, max0 = np.where(r)[0][[0, -1]]
    min1, max1 = np.where(c)[0][[0, -1]]
    min2, max2 = np.where(z)[0][[0, -1]]

    template_crop = template[min0:max0, min1:max1, min2:max2]
    parcel_crop = slic(template_crop, n_segments=args.segments, compactness=args.compactness, multichannel=False, spacing=template_sitk.GetSpacing()[::-1])

    parcel = np.zeros(template.shape, dtype=np.int64)
    parcel[min0:max0, min1:max1, min2:max2] = parcel_crop
    parcel[~mask] = 0

else:

    parcel = np.zeros(template.shape, dtype=np.int64)
    parcel[mask] = 1

print "Number of parcels {}".format(np.unique(parcel).size - 1)

aux_sitk = sitk.GetImageFromArray(parcel.astype(np.int32))
aux_sitk.CopyInformation(template_sitk)
sitk.WriteImage(aux_sitk, args.parcel_file)

pass