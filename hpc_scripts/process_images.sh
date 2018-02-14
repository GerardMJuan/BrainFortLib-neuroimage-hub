#!/bin/bash
#SBATCH -J process_img
#SBATCH -p default
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o process_img_%J.out # STDOUT
#SBATCH -e process_img_%j.err # STDERR

module load Python/2.7.12-foss-2017a

#python -u /homedtic/gmarti/CODE/register_and_process/process_images.py  --in_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/FOLLOWUPS_b/ --img_suffix .nii --n4 --denoising --histmatch --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --template_norm --out_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/FOLLOWUPS/
python -u /homedtic/gmarti/CODE/img-mri-processing/MRI_processing/process_images.py  --in_dir /homedtic/gmarti/DATA/Data/ADNI/ --in_metadata /homedtic/gmarti/DATA/ADNImetadata/ADNI/ADNI_Standard_Baselines.csv --img_suffix .nii --n4 --denoising --histmatch --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --template_norm --out_dir /homedtic/gmarti/DATA/Data/ADNI_SD_B/ --num_threads 50
