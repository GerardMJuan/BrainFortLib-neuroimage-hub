#!/bin/bash
#SBATCH -J hipp
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o LOGS/regbas%J.out # STDOUT
#SBATCH -e LOGS/regbas%j.err # STDERR

source /etc/profile.d/lmod.sh
source /etc/profile.d/easybuild.sh

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn


BASE_DIR='/homedtic/gmarti/DATA/Hippo_PMaragall/'	    # dir containing BIDS data
SCRIPTS_DIR="/homedtic/gmarti/CODE/upf-nii/scripts/old_scripts"	# dir containing the scripts
TEMPLATE="/homedtic/gmarti/DATA/Hippo_PMaragall/template/template_img.nii.gz"
LABELS_suffix="_labels.nii.gz"
TEMPLATE_LABEL="/homedtic/gmarti/DATA/Hippo_PMaragall/template/template_lab.nii.gz"

# python $SCRIPTS_DIR/register_to_template.py  --in_dir $BASE_DIR/T1_nii/ --img_suffix _img.nii.gz --out_dir $BASE_DIR/reg/ --transform Syn* 1 --template_file $TEMPLATE --out_warp_intfix reg --output_warped_image --use_labels $BASE_DIR/labels/ $LABELS_suffix $TEMPLATE_LABEL 0.5

BASE_DIR='/homedtic/gmarti/DATA/Data/'	    # dir containing BIDS data
SCRIPTS_DIR="/homedtic/gmarti/CODE/upf-nii/scripts"	# dir containing the scripts
TEMPLATE="/homedtic/gmarti/DATA/Hippo_PMaragall/template/template_img.nii.gz"
LABELS_suffix="_labels.nii.gz"
TEMPLATE_LABEL="/homedtic/gmarti/DATA/Hippo_PMaragall/template/template_lab.nii.gz"

python $SCRIPTS_DIR/register_to_template_BIDS.py  --in_dir $BASE_DIR/ADNI35_PRACTICAMIA/ --img_suffix .nii.gz --out_name $BASE_DIR/hipp_pmaragall/ --transform Syn* 1 --template_file $TEMPLATE --out_warp_intfix reg --output_warped_image --number_jobs 35
