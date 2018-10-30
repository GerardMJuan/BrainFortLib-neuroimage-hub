#!/bin/bash
# Segment image
#SBATCH -J segment
#SBATCH -p short
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o segment_%J.out # STDOUT
#SBATCH -e sgement_%j.err # STDERR

module load Python/3.6.4-foss-2017a

module load python
python3 /homedtic/gmarti/CODE/upf-neuroimage-preprocess-hub/scripts/segment_images.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_Affine1_SdBaseline_masked/ --out_dir /homedtic/gmarti/DATA/Data/ADNI_Affine1_SdBaseline_seg/ --img_suffix Warped.nii.gz --num_threads 40
