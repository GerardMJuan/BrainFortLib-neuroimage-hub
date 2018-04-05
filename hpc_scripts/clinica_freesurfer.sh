#!/bin/bash
#SBATCH -J free
#SBATCH -p high
#SBATCH -N 1
#SBATCH -n 4
#SBATCH -w node021
#SBATCH --workdir=/homedtic/gmarti
#SBATCH -o free_%J.out # STDOUT
#SBATCH -e free_%j.err # STDERR

module load MATLAB
source /homedtic/gmarti/ENV/clinica/bin/activate
FSLDIR=/homedtic/gmarti/LIB/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
export PATH=${FSLDIR}/bin:${PATH}
export PATH="~/.local/bin:$PATH"
export PATH="~/bin:$PATH"
export FREESURFER_HOME=/homedtic/gmarti/LIB/freesurfer
. $FREESURFER_HOME/SetUpFreeSurfer.sh

clinica run t1-freesurfer-cross-sectional /homedtic/gmarti/DATA/Data/ADNI_BIDS_NOTEMPTY/ /homedtic/gmarti/DATA/Data/ADNI_FREE/ -tsv /homedtic/gmarti/DATA/Data/participants_small.tsv -np 4
#clinica run t1-freesurfer-cross-sectional /homedtic/gmarti/DATA/Data/ADNI_BIDS_NOTEMPTY/ /homedtic/gmarti/DATA/Data/ADNI_FREE/ -tsv /homedtic/gmarti/DATA/Data/participants_small.tsv
