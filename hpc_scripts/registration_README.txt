# ADNI registration instructions

This file describes how to do a proper registration from a normally downloaded dataset from the ADNI website to a properly registered dataset.

## Getting Started

In this file we will describe the commands we have to use, and the order in which we have to use them, to register a database of brain MRI image.

### Prerequisites

* Have a .csv file of the database, detailing the directory of each image
* Export the scheduler.py in the mod_py directory to the python PATH

* Python3

### Instructions

1. Preprocess all the images, using the file process_image_fromfile.py

This script does normalization, deonising, histogram matching, normalization with respect tot a template, and divides the output files in two different directories, one for baselines and another one for followups.

Example of execution:

python process_images_fromfile.py  --in_dir /homedtic/gmarti/DATA/Data/ --in_metadata /homedtic/gmarti/DATA/Data/metadataADNI_paths.csv --img_suffix .nii --n4 --denoising --histmatch --template_file /homedtic/gsanroma/DATA/DATABASES/ADNI/atlases/templates/template_adni.nii.gz --template_norm --out_dir_baseline /homedtic/gmarti/DATA/Data/baseline_processed/ --out_dir_followups /homedtic/gmarti/DATA/Data/followups_processed/

2. Register the followups to each baseline

We need to register the followups to each corresponding baseline. Preferred is to do an Affine 4 transformation. Use register_to_baseline.py

Example of execution:

register_to_baseline.py --in_dir /homedtic/gmarti/DATA/Data/followups_processed/ --img_suffix .nii --template_dir  /homedtic/gmarti/DATA/Data/baseline_processed/ --transform Affine 4 --out_warp_intfix aff4 --out_dir  /homedtic/gmarti/DATA/Data/followups_baseline_reg/ --output_warped_image

3. Register both the followups and the baseline to the template

Using a given template. Preferable a NOn-rigid transformation, Syn 1-4. Use register_to_template.py

register_to_template.py --in_dir /homedtic/gmarti/DATA/Data/baseline_processed/ --img_suffix .nii.gz --template_file /homedtic/gsanroma/DATA/DATABASES/ADNI/atlases/templates/template_adni.nii.gz --transform Syn 1 --out_warp_intfix syn1 --out_dir /homedtic/gmarti/DATA/Data/toTemplate_Syn1 --output_warped_image

4. Mask the image to remove the bones

Given an input directory and an output directory, remove the bones by just masking the image. It is not a proper bone-removal algorithm. Use createmask.py

Example of execution:

python3 createmask.py --template_mask icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii --in_dir baseline_toTemplate_Syn2/ --out_dir baseline_Syn2_masked/ --img_suffix Warped.nii.gz


# Author
* **Gerard Martí** - (gerard.marti@upf.edu)
