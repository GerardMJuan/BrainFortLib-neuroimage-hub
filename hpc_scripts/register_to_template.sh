#!/bin/bash
#SBATCH -J register_baseline
#SBATCH -p short
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o reg_b_%J.out # STDOUT
#SBATCH -e reg_b_%J.err # STDERR
module load Python/2.7.12-foss-2017a

python -u /homedtic/gmarti/CODE/register_and_process/register_to_template.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_TEST/ --img_suffix .nii.gz --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --transform Syn* 2 --out_warp_intfix rigid1 --out_dir  /homedtic/gmarti/DATA/Data/ADNI_TEST/ --output_warped_image
