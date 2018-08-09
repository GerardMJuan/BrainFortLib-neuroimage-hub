#!/bin/bash
#SBATCH -J reg
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o LOGS/reg%J.out # STDOUT
#SBATCH -e LOGS/reg%j.err # STDERR

source /etc/profile.d/lmod.sh
source /etc/profile.d/easybuild.sh
module load libGLU

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn

BASE_DIR="/homedtic/gmarti/DATA/Data/ADNI_BIDS"	    # dir containing BIDS data
SCRIPTS_DIR="/homedtic/gmarti/CODE/upf-nii/scripts"	# dir containing the scripts
N_THREADS="75"                                       # N of threads for parallel comp.
TEMPLATE="/homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI_brain_rescaled.nii"

# python $SCRIPTS_DIR/robex_brain_extraction_BIDS.py  --input_dir $BASE_DIR/derivatives/denoised/ --out_dir $BASE_DIR/derivatives/robex --input_suffix .nii.gz --number_jobs $N_THREADS

python $SCRIPTS_DIR/register_to_template_BIDS.py  --in_dir $BASE_DIR/ --in_name space_baseline/ --img_suffix .nii.gz --out_name space_ffd20 --transform BSplineSyN* 2 --c_point 20 --template_file $TEMPLATE --out_warp_intfix ffd20 --output_warped_image --number_jobs $N_THREADS --baseline

# python $SCRIPTS_DIR/register_to_template_BIDS.py  --in_dir $BASE_DIR/ --in_name space_baseline/ --img_suffix .nii.gz --out_name space_affine --transform Affine* 2 --template_file $TEMPLATE --out_warp_intfix aff --output_warped_image --number_jobs $N_THREADS
