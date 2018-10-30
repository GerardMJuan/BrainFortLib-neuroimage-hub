#!/bin/bash
#SBATCH -J free
#SBATCH -p high
#SBATCH -N 14
#SBATCH -n 1
#SBATCH --workdir=/homedtic/gmarti
#SBATCH -o LOGS/free_%J.out # STDOUT
#SBATCH -e LOGS/free_%j.err # STDERR

module load MATLAB
module load libGLU
# module load Python/2.7.12-foss-2017a
export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn
FSLDIR=/homedtic/gmarti/LIB/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
export PATH=${FSLDIR}/bin:${PATH}
# export PYTHONPATH="/homedtic/gmarti/ENV/python2.7:$PYTHONPATH"
export PATH="~/.local/bin:$PATH"
export PATH="~/bin:$PATH"
export FREESURFER_HOME=/homedtic/gmarti/LIB/freesurfer
. $FREESURFER_HOME/SetUpFreeSurfer.sh
SECONDS=0

python /homedtic/gmarti/CODE/upf-nii/scripts/recon_all_BIDS_long.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_BIDS --img_suffix .nii.gz --output_path /homedtic/gmarti/DATA/Data/CIMLR-long --subject_file /homedtic/gmarti/DATA/ADNImetadata/simlrad-paper/freesurfer_information_long.csv --number_jobs 30

duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
