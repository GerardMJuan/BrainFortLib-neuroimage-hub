#!/bin/bash
#SBATCH -J sim
#SBATCH -p high
#SBATCH -N 4
#SBATCH --ntasks-per-node=16
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o LOGS/sim%J.out # STDOUT
#SBATCH -e LOGS/sim%j.err # STDERR

source /etc/profile.d/lmod.sh
source /etc/profile.d/easybuild.sh
module load libGLU

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn

BASE_DIR="/homedtic/gmarti/DATA/Data/ADNI_BIDS"	    # dir containing BIDS data
SCRIPTS_DIR="/homedtic/gmarti/CODE/upf-nii/scripts"	# dir containing the scripts
N_THREADS="60"                                       # N of threads for parallel comp.
TEMPLATE="/homedtic/gmarti/DATA/MNI152/icbm_avg_152_t1_tal_nlin_symmetric_VI.nii"

python /homedtic/gmarti/CODE/upf-nii/scripts/compute_similarities_BIDS.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_BIDS/derivatives/space_aff/ --img_suffix .nii.gz --method Correlation --out_file /homedtic/gmarti/pair_sim_aff --number_jobs 50 --number_cpus 16
