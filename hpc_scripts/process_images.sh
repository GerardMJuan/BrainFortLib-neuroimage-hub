#!/bin/bash
#SBATCH -J process_img
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o process_img_%J.out # STDOUT
#SBATCH -e process_img_%j.err # STDERR

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn
python /homedtic/gmarti/CODE/upf-nii/scripts/process_images_BIDS.py  --in_dir /homedtic/gmarti/DATA/Data/ADNI_BIDS/ --denoising --out_dir /homedtic/gmarti/DATA/Data/ADNI_BIDS/derivatives/denoised/ --num_threads 10

#python -u /homedtic/gmarti/CODE/register_and_process/process_images.py  --in_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/FOLLOWUPS_b/ --img_suffix .nii --n4 --denoising --histmatch --template_file /homedtic/gmarti/DATA/MNI  152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --template_norm --out_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/FOLLOWUPS/
# python /homedtic/gmarti/CODE/img-mri-processing/MRI_processing/process_images.py  --in_dir /homedtic/gmarti/DATA/Data/ADNI_STANDARD/ --in_metadata /homedtic/gmarti/DATA/ADNIMRIStandard1.5/StandardFull.csv --img_suffix .nii --denoising --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --template_norm --out_dir /homedtic/gmarti/DATA/Data/ADNI_SD_preprocessed/ --num_threads 3
