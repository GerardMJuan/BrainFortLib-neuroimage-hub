import argparse
import os
import SimpleITK as sitk
import numpy as np
from scipy.ndimage.morphology import distance_transform_edt

parser = argparse.ArgumentParser()
parser.add_argument("--in_mask", type=str, nargs=1, required=True)
parser.add_argument("--in_region", type=str, nargs=1, required=True)
parser.add_argument("--out_parcel", type=str, nargs=1, required=True)

# args = parser.parse_args()
img = 'iugr093'
# args = parser.parse_args('--in_mask /Users/gsanroma/DATA/DATABASES/Fetal/corrected/{0}_ctx.nii.gz --in_region /Users/gsanroma/DATA/DATABASES/Fetal/corrected/tpl_warped/{0}XtplInvwarped.nii.gz --out_parcel /Users/gsanroma/DATA/DATABASES/Fetal/corrected/{0}_ctxreg.nii.gz'.format(img).split())
args = parser.parse_args('--in_mask /Users/gsanroma/DATA/DATABASES/NeoMater/targets_seg_ens/wm/{0}_wm.nii.gz --in_region /Users/gsanroma/DATA/DATABASES/NeoMater/targets_seg_ens/regions/{0}_cortex_regions.nii.gz --out_parcel /Users/gsanroma/DATA/DATABASES/NeoMater/targets_seg_ens/wm_reg/{0}_wmreg.nii.gz'.format(img).split())

mask_sitk = sitk.ReadImage(args.in_mask[0])
region_sitk = sitk.ReadImage(args.in_region[0])

assert mask_sitk.GetSize() == region_sitk.GetSize(), "Region and mask must be of same size"

mask = sitk.GetArrayFromImage(mask_sitk)
region = sitk.GetArrayFromImage(region_sitk)

u_reg = np.unique(region)
u_reg = np.delete(u_reg, np.where(u_reg == 0))

print "Computing distance maps"
DMAPS = np.zeros((u_reg.size,) + mask.shape, dtype=np.float32)
for i, id_reg in enumerate(list(u_reg)):
    DMAPS[i,...] = distance_transform_edt(np.invert(region == id_reg), region_sitk.GetSpacing()[::-1])

print "Parcellating"
parcel = np.zeros(region.shape, dtype=region.dtype)
I0, I1, I2 = np.nonzero(mask)
for i0, i1, i2 in zip(I0, I1, I2):
    parcel[i0, i1, i2] = u_reg[np.argmin(DMAPS[:, i0, i1, i2])]

parcel_sitk = sitk.GetImageFromArray(parcel)
parcel_sitk.CopyInformation(mask_sitk)
sitk.WriteImage(parcel_sitk, args.out_parcel[0])