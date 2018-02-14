#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This program generates a series of images obtained by removing the baseline from the followup images, to obtain the evolution of 
each followup. The images are registered to the baseline and to the template
"""

import argparse
import os
import time
import SimpleITK as sitk
import pickle
import numpy as np
from fnmatch import fnmatch

__author__ = "Gerard Martí"
__email__ = "gerard.marti@upf.edu"
__license__ = "GNU"
__version__ = "0.1"

parser = argparse.ArgumentParser(description='Process all the images on the specified directory and save the information in a file')
parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='directory input images')
parser.add_argument("--out_directory", type=str, nargs=1, required=True, help='directory where the features are stored')
parser.add_argument("--img_suffix",type=str, nargs=1, required=True, help='suffix input images')
parser.add_argument("--out_suffix", type=str, nargs=1, required=True, help='suffix for the out images')
args = parser.parse_args()

'''
# Example of an execution:
python3 substract_baseline.py --in_dir /homedtic/gmarti/DATA/ADNI_followup/baselines_MNI_Syn1/ --out_directory /homedtic/gmarti/DATA/ADNI_followup/MNI_Syn1_subsFromBaseline/ --img_suffix nii.gz --out_suffix .subs
 '''


def main():
    """Main function of the program.

    Reads the data, and substracts each image from its baseline
    """
    # Get data
    reg_dir = args.in_dir[0]
    out_path = args.out_directory[0]
    os.makedirs(out_path, exist_ok=True)
    
    # Load the images in order
    
    files_list = os.listdir(reg_dir)
    img_directories = [os.path.join(args.in_dir[0], f) for f in sorted(files_list) if fnmatch(f, '*' + args.img_suffix[0])]

    baseline = None
    curr_RID = 0
    for img_path in img_directories:
        rid_index = img_path.find('_S_')
        RID = int(img_path[rid_index+3:rid_index+7])
        img_sitk = sitk.ReadImage(img_path)
        img = sitk.GetArrayFromImage(img_sitk)
        img = np.asarray(img)   # If its a new subject, update the baseline
        if RID != curr_RID:
            print('Setting baseline to ' + str(RID))
            curr_RID = RID
            baseline = img
        else:
            img = img - baseline
            img[np.where(img<0)] = 0
            # Save the image to disk
            img = sitk.GetImageFromArray(img)
            savepath = out_path + os.path.basename(img_path[:-7]) + args.out_suffix[0] + '.' + args.img_suffix[0]
            print('Print file to ' + savepath)

            sitk.WriteImage( sitk.Image(img), savepath)


if __name__ == "__main__":
    main()

