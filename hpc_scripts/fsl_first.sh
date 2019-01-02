#!/bin/bash
#SBATCH -J fsl
#SBATCH -p high
#SBATCH --mem 10G
#SBATCH --workdir=/homedtic/gmarti/
#SBATCH -o LOGS/first%J.out # STDOUT
#SBATCH -e LOGS/first%j.err # STDERR

source /etc/profile.d/lmod.sh
source /etc/profile.d/easybuild.sh
module load libGLU

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn

FSLDIR=/homedtic/gmarti/LIB/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH

run_first_all -i /homedtic/gmarti/DATA/Data/quick_first_test/sub-ADNI002S0295_ses-M00_T1w.nii.gz -o /homedtic/gmarti/DATA/Data/quick_first_test/segmented
