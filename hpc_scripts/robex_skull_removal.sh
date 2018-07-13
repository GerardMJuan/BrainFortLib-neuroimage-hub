#!/bin/bash
#SBATCH -J robex
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o skull_pipeline%J.out # STDOUT
#SBATCH -e skull_pipeline%j.err # STDERR

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn

BASE_DIR="/homedtic/gmarti/DATA/Data/ADNI_BIDS"	    # dir containing BIDS data
SCRIPTS_DIR="/homedtic/gmarti/CODE/upf-nii/scripts"	# dir containing the scripts
N_THREADS="40"                                       # N of threads for parallel comp.

python $SCRIPTS_DIR/robex_brain_extraction_BIDS.py  --input_dir $BASE_DIR/ --out_dir $BASE_DIR/derivatives/robex --input_suffix .nii.gz --strip_suffix _r.nii.gz --number_jobs $N_THREADS
