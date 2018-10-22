#!/bin/bash
# Register to baseline, BUT NEED TO UPDATE IT TO register_to_baseline_BIDS
# DO NOT USE IT AS IT IS
#SBATCH -J register_baseline
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o reg_b_%J.out # STDOUT
#SBATCH -e reg_b_%j.err # STDERR

module load Python/3.6.4-foss-2017a

python -u register_to_baseline.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_SUBSET/baseline_mini/ --img_suffix .nii --template_file /homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii --transform Rigid 1 --out_warp_intfix rigid1 --out_dir  /homedtic/gmarti/DATA/Data/ADNI_SUBSET/baseline_mini_r/ --output_warped_image
