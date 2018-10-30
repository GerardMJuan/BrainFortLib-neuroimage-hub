"""
Check which images are available.

Script that looks at the ADNIMERGE file and checks how many of the
subjects have either a MRI or a PET scan downloaded. It also checks for
the same file existance in the BIDS directory. The output of this Script is
a .csv file with the availabiliy information of all subjects mentioned in ADNIMERGE.
"""

import pandas as pd
import os
import shutil
import glob
import bids.layout
import bids.tests

# Path to ADNIMERGE and directories
ADNIMERGE_file = "/homedtic/gmarti/DATA/ADNIMRIStandard1.5/ADNIMERGE.csv"
BIDS_DIR = "ADNI_BIDS/"
ADNI_DIR = "ADNI/"

# Load ADNIMERGE
df_adnimerge = pd.read_csv(ADNIMERGE_file)

# Get only PTID, month and study columns
df_metadata = df_adnimerge[["PTID", "VISCODE", "COLPROT", "IMAGEUID"]].copy()

# Get BIDS directory info with layouts
layout = bids.layout.BIDSLayout(BIDS_DIR)
assert len(layout.get_subjects()) > 0, "No subjects in directory!"

# Create empty lists with the availability
# These will contain either "Yes" or "No" depending on availability
MRI_ADNI = []
PET_ADNI = []
MRI_BIDS = []
PET_BIDS = []

# for each line:
for row in df_adnimerge.itertuples():

    PET_BIDS.append('No')
    PET_ADNI.append('No')
    subj = row.PTID
    # Image.id is the third field (corrseponding to 2) of the row.
    try:
        imageid = str(int(row.IMAGEUID))
    except:
        MRI_ADNI.append("No")
        MRI_BIDS.append("No")
        continue
    f = glob.glob(ADNI_DIR + subj + "/*/*/*/*I" + imageid + ".nii")
    # if found, add information to columns
    if f:
        MRI_ADNI.append("Yes")
    # If not, add missing data
    else:
        MRI_ADNI.append("No")

    # Test for BIDS
    # Get session name
    session = ''
    if row.VISCODE == 'bl':
        session = 'M00'
    else:
        session = 'M' + row.VISCODE[1:]
    patient_id = 'ADNI' + subj[0:3] + 'S' + subj[6:]
    imgs = layout.get(subject=patient_id, modality='anat', session=session)
    # If exists
    if imgs:
        MRI_BIDS.append("Yes")
    else:
        MRI_BIDS.append("No")

df_metadata.loc[:, "MRI_ADNI"] = MRI_ADNI
df_metadata.loc[:, "PET_ADNI"] = PET_ADNI
df_metadata.loc[:, "MRI_BIDS"] = MRI_BIDS
df_metadata.loc[:, "PET_BIDS"] = PET_BIDS
df_metadata.to_csv("summary_files.csv")
