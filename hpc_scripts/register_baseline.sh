#!/bin/bash
#SBATCH -J register_baseline
#SBATCH -p default
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o reg_b_%J.out # STDOUT
#SBATCH -e reg_b_%j.err # STDERR

module load Python/3.6.4-foss-2017a

python3 -u /homedtic/gmarti/CODE/img-mri-processing/MRI_processing/register_to_template.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_SD_B/ --in_metadata /homedtic/gmarti/DATA/ADNImetadata/ADNI/ADNI_Standard_Baselines.csv --img_suffix .nii --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --transform Affine 1 --out_warp_intfix affine1 --out_dir /homedtic/gmarti/DATA/Data/ADNI_Affine1_SdBaseline/ --output_warped_image --clean --num_threads 80
#python -u register_to_template.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/BASELINE/ --img_suffix .nii --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --transform Rigid 1 --out_warp_intfix rigid1 --out_dir  /homedtic/gmarti/DATA/Data/ADNI_SUBSET/baseline_R/ --output_warped_image
#python -u register_to_baseline.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/baseline_mini/ --img_suffix .nii --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --transform Rigid 1 --out_warp_intfix rigid1 --out_dir  /homedtic/gmarti/DATA/Data/ADNI_SUBSET/baseline_mini_r/ --output_warped_image
