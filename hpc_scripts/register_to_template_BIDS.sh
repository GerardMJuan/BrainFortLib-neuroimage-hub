#!/bin/bash
#SBATCH -J register_template
#SBATCH -p short
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o reg_b_%J.out # STDOUT
#SBATCH -e reg_b_%J.err # STDERR
module load Python/2.7.12-foss-2017a

python -u /homedtic/gmarti/CODE/upf-nii/scripts/register_to_template_BIDS.py --in_dir /homedtic/gmarti/DATA/Data/BIDS_TEST --img_suffix .nii.gz --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --transform Affine 1 --out_warp_intfix rigid1 --output_warped_image
