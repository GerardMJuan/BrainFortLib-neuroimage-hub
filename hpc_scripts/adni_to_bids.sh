#!/bin/bash
# This script runs the clinica script adni-to-bids. Need to have clinica installed. More information about
# clinica can be found in: http://www.clinica.run/

#SBATCH -J adni_to_bids
#SBATCH -p medium
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o bids_%J.out # STDOUT
#SBATCH -e bids_%j.err # STDERR

module load Python/2.7.12-foss-2017a
module load MATLAB

# Load all the software we need to include
source /homedtic/gmarti/ENV/clinica/bin/activate
FSLDIR=/homedtic/gmarti/LIB/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
PATH=${FSLDIR}/bin:${PATH}
export FSLDIR PATH
export PATH="~/.local/bin:$PATH"
export PATH=$PATH:/homedtic/gmarti/LIB/lx/mricron_lx
export PATH=$PATH:/homedtic/gmarti/LIB/dcm2niix-master/bin/bin
export ANTSPATH=/homedtic/gmarti/LIB/ANTsbin/bin
export ANTSSCRIPTS=/homedtic/gmarti/LIB/ANTs/Scripts
export PATH=${ANTSPATH}:${PATH}
export SPM_HOME=/homedtic/gmarti/LIB/spm12

#echo "Does it work?"
clinica convert adni-to-bids /homedtic/gmarti/DATA/Data/ADNI /homedtic/gmarti/DATA/Data/ADNI_CLINICALDATA/ /homedtic/gmarti/DATA/Data/ADNI_BIDS_NOTEMPTY/
