#!/bin/bash
# Full script to remove skull DO NOT USE, NEEDS UPDATING.
#SBATCH -J pipeline
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/DATA/Data
#SBATCH -o skull_pipeline%J.out # STDOUT
#SBATCH -e skull_pipeline%j.err # STDERR

# Load of modules
module load Python/2.7.12-foss-2017a
module load SimpleITK/1.0.1-foss-2017a-Python-3.6.4
export PYTHONPATH="/homedtic/gmarti/ENV/python2.7:$PYTHONPATH"

# Variables
BASE_DIR="/homedtic/gmarti/DATA/Data/ADNI_BIDS"	    # dir containing BIDS data
SCRIPTS_DIR="/homedtic/gmarti/CODE/upf-nii/scripts"	# dir containing the scripts
N_THREADS="60"                                       # N of threads for parallel comp.
TEMPLATE="/homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii"
MASK_TEMPLATE="/homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii"

# Denoising
printf "Denoising, N4, hist norm...\n"
python $SCRIPTS_DIR/process_images_BIDS.py  --in_dir $BASE_DIR/ --denoising --out_dir $BASE_DIR/derivatives/denoised/ --num_threads $N_THREADS

# --template_file $TEMPLATE

# Register baselines to template
printf "Register to template...\n"
python $SCRIPTS_DIR/register_to_template_BIDS.py  --in_dir $BASE_DIR/ --in_name denoised/ --img_suffix .nii.gz --out_name registered --transform Syn* 1 --template_file $TEMPLATE --out_warp_intfix syn1  --output_warped_image --number_jobs $N_THREADS --baseline


# Use rigid/affine transformation from followup to BL (affine seems more likely).
echo "Register to baseline..."
python $SCRIPTS_DIR/register_to_baseline_BIDS.py  --in_dir $BASE_DIR/ --in_name robex/ --img_suffix .nii.gz --out_name registered_baseline --transform Affine* 1 --out_warp_intfix aff1 --output_warped_image --number_jobs $N_THREADS

# Use inverse of registers to propagate the mask of the template to each baseline.
echo "Propagate mask to baseline..."
python $SCRIPTS_DIR/propagate_mask_template.py  --in_dir $BASE_DIR/ --in_name registered/ --img_suffix Warped.nii.gz --reg_suffix 0GenericAffine.mat --template_mask $MASK_TEMPLATE --out_name regmasks --ref_name denoised/ --out_warp_intfix regmask --number_jobs $N_THREADS

# Propagate the mask to follow-ups.
echo "Propagate mask to followup..."
python $SCRIPTS_DIR/propagate_mask_followups.py --in_dir $BASE_DIR/ --in_name regmasks/ --img_suffix Warped.nii.gz --reg_suffix 0GenericAffine.mat --ref_name denoised/ --reg_name registered/ --out_warp_intfix regmask

# Remove cranium.
# Adapt from compute_mask.py
echo "Apply mask..."
python $SCRIPTS_DIR/remove_skull.py --base_dir $BASE_DIR/ --mask_name regmasks/ --img_name denoised/  --out_name noskull/ --dilation_radius 5

# N4 correction and histogram matching.
# echo "N4 correction and hist matching..."
# python $SCRIPTS_DIR/process_images_BIDS.py  --in_dir $BASE_DIR/derivatives/noskull/ --histmatch --template_norm --out_dir $BASE_DIR/derivatives/corrected/ --num_threads $N_THREADS --norm

echo "Done!"
