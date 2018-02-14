#!/bin/bash
#SBATCH -J masking
#SBATCH -p short
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o mask_%J.out # STDOUT
#SBATCH -e mask_%J.err # STDERR
module load Python/3.6.4-foss-2017a

python3 /homedtic/gmarti/CODE/img-mri-processing/MRI_processing/createmask.py --template_mask /homedtic/gmarti/DATA/Data/icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii --in_dir /homedtic/gmarti/DATA/Data/ADNI_Affine1_SdBaseline/ --out_dir /homedtic/gmarti/DATA/Data/ADNI_Affine1_SdBaseline_masked/ --img_suffix Warped.nii.gz --dilate --size 3
