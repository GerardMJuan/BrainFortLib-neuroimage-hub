"""
ADNI_to_BIDS main script.

This script converts an input ADNI raw directory, downloaded to the website, to a BIDS-based
directory. BIDS is a neuroimage directory format specially designed for reproducibility and
clarity. For more information, visit: http://bids.neuroimaging.io/

Code by: Gerard Martí Juan (gerard.marti@upf.edu)
Some of the code and ideas is taken from the Clinica software (clinica.run)
"""

import argparse
import os
from fnmatch import fnmatch
from libs.scheduler import Launcher
import pandas as pd
import numpy as np
import time

def get_parser():
    """
    Create the parser.

    Creates and returns the parser that will gather the input of the function.
    This is an auxiliary function so that this script can both be
    called from Python interpreter and from other scripts.
    """
    parser = argparse.ArgumentParser(description='Converts ADNI directory to BIDS.')
    parser.add_argument("--in_dir", type=str, nargs=1, required=True, help='ADNI directory of raw data')
    parser.add_argument("--metadata_file", type=str, nargs=1, required=True, help='ADNIMERGE file, from the ADNI website, location')
    parser.add_argument("--img_suffix", type=str, nargs=1, required=True, help='suffix of input images')
    parser.add_argument("--out_dir", type=str, nargs=1, required=True, help="Output directory where to store the resulting directories.")
    parser.add_argument("--validate", action="store_true", help='Validate the dataset after finishing')
    parser.add_argument("--convert_img", action="store_true", help='Convert the images to .nii.gz format')
    return parser


def main(in_dir, metadata, img_suffix, out_dir, validate=False, convert=False):
    """
    Main function of the program.

    Reads the input files, creates the new directories, and
    validates the data if asked.
    """
    t0 = time.time()
    # Read input directory

    subject_list = []
    # For each found subject, create directory
    for subj in subject_list:
        do = 'something'
    # Move and convert the data, if applicable

    # Validate it
    if validate:
        validate = 'it'
    print('Conversion to BIDS finished.')
    t1 = time.time()
    print('Time to compute the script: ', t1 - t0)



if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()
    main(args.in_dir[0], args.metadata_file[0], args.img_suffix[0],
         args.out_dir[0], args.validate, args.convert_img)
