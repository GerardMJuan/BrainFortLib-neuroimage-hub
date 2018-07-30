"""
Quick script to move some files.

Not really important.
"""

from bids.grabbids import BIDSLayout
import argparse
import os
from shutil import copy2

OG_DIR = "/homedtic/gmarti/DATA/Data/ADNI_BIDS/derivatives/robex"
NEW_DIR = "/homedtic/gmarti/DATA/Data/ADNI_BIDS/derivatives/registered_baseline"

# Move baselines from OG dir to new dir

layout_og = BIDSLayout(OG_DIR)
layout_new = BIDSLayout(NEW_DIR)

files = layout_og.get(session='M00', extensions='.nii.gz')

for img in files:
    img_path = img.filename
    img_file = os.path.basename(img_path)

    out_dir_img = NEW_DIR + '/' + img.subject + '/' + img.session + '/' + img.modality + '/'

    if not os.path.exists(out_dir_img):
        os.makedirs(out_dir_img)

    print(out_dir_img + img_file)
    copy2(img_path, out_dir_img + img_file)
