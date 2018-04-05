#!/bin/bash
#SBATCH -J spm12
#SBATCH -p high
#SBATCH -N 4
#SBATCH -n 8
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o spm_%J.out # STDOUT
#SBATCH -e spm_%j.err # STDERR

module load Python/2.7.12-foss-2017a
module load MATLAB
source /homedtic/gmarti/ENV/clinica/bin/activate

FSLDIR=/homedtic/gmarti/LIB/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
export PATH=${FSLDIR}/bin:${PATH}
export PATH="~/.local/bin:$PATH"
export PATH=$PATH:/homedtic/gmarti/LIB/lx/mricron_lx
export PATH=$PATH:/homedtic/gmarti/LIB/dcm2niix-master/bin/bin
export ANTSPATH=/homedtic/gmarti/LIB/ANTsbin/bin
export ANTSSCRIPTS=/homedtic/gmarti/LIB/ANTs/Scripts
export PATH=${ANTSPATH}:${PATH}
export SPM_HOME=/homedtic/gmarti/LIB/spm12

export FREESURFER_HOME=/usr/local/freesurfer
source $FREESURFER_HOME/SetUpFreeSurfer.sh

clinica run t1-spm-full-prep /homedtic/gmarti/DATA/Data/ADNI_BIDS_NOTEMPTY/ /homedtic/gmarti/DATA/Data/ADNI_SPM/ posterDTIC -tsv /homedtic/gmarti/DATA/Data/participants_small.tsv
