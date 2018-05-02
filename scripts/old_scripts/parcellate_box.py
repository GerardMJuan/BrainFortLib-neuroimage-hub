
import SimpleITK as sitk
import numpy as np
from scipy.ndimage.morphology import binary_dilation
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("mask_file",type=str)
parser.add_argument("downscale_factor",type=float)
parser.add_argument("out_file",type=str)

args = parser.parse_args()
# args = parser.parse_args(['/Users/gsanroma/DATA/DATABASES/NeoBrainS12/30w/template_mask.nii.gz','8','/Users/gsanroma/DATA/stacking/NB30_data/template_parcel.nii.gz'])
# args = parser.parse_args('/Users/gsanroma/DATA/DATABASES/NeoMater/templates/mask_isotropic.nii.gz 8 /Users/gsanroma/DATA/stacking/NeoMater/parcellations/parcel08.nii.gz'.split())

mask_sitk = sitk.ReadImage(args.mask_file)

scale = sitk.ScaleTransform(3)
scale.SetScale((args.downscale_factor, args.downscale_factor, args.downscale_factor))

resample = sitk.ResampleImageFilter()
resample.SetReferenceImage(mask_sitk)
resample.SetTransform(scale)
resample.SetInterpolator(sitk.sitkNearestNeighbor)

shrink_sitk = resample.Execute(mask_sitk)

shrink = sitk.GetArrayFromImage(shrink_sitk).astype(np.bool)
shrink = binary_dilation(shrink)

i0,i1,i2 = np.nonzero(shrink)
i0 = i0.astype(np.uint16); i1 = i1.astype(np.uint16); i2 = i2.astype(np.uint16)
I = np.ravel_multi_index((i0, i1, i2), shrink.shape)
Npar = I.size + 1

print "Number of parcels: {}".format(Npar)

parcels = np.zeros(shrink.shape, dtype=np.int32)
parcels.ravel()[I] = np.arange(1, Npar, dtype=np.int32)

parcels_sitk = sitk.GetImageFromArray(parcels)
parcels_sitk.CopyInformation(mask_sitk)

scale.SetScale((1./args.downscale_factor, 1./args.downscale_factor, 1./args.downscale_factor))
resample.SetTransform(scale)

expand_sitk = resample.Execute(parcels_sitk)

sitk.WriteImage(expand_sitk, args.out_file)

pass

