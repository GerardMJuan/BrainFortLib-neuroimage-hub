#!/bin/bash
#SBATCH -J free
#SBATCH -p medium
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --workdir=/homedtic/gmarti
#SBATCH -o LOGS/free_%J.out # STDOUT
#SBATCH -e LOGS/free_%j.err # STDERR

module load MATLAB
module load libGLU
module load Python/2.7.12-foss-2017a
FSLDIR=/homedtic/gmarti/LIB/fsl
. ${FSLDIR}/etc/fslconf/fsl.sh
export PATH=${FSLDIR}/bin:${PATH}
export PYTHONPATH="/homedtic/gmarti/ENV/python2.7:$PYTHONPATH"
export PATH="~/.local/bin:$PATH"
export PATH="~/bin:$PATH"
export FREESURFER_HOME=/homedtic/gmarti/LIB/freesurfer
. $FREESURFER_HOME/SetUpFreeSurfer.sh
SECONDS=0

python /homedtic/gmarti/CODE/upf-nii/scripts/recon_all_BIDS.py --in_dir /homedtic/gmarti/DATA/Data/ADNI_BIDS --img_suffix .nii.gz --output_path /homedtic/gmarti/DATA/Data/SIMLR-AD-FS_Full --subject_file /homedtic/gmarti/DATA/ADNImetadata/simlrad-paper/freesurfer_information.csv --number_jobs 30
#recon-all -i /homedtic/gmarti/DATA/Data/BIDS_TEST/sub-ADNI002S0295/ses-M00/anat/sub-ADNI002S0295_ses-M00_T1w.nii.gz -s ADNI002S0295 -sd /homedtic/gmarti/DATA/Data/output_freesurfer -all
# clinica run t1-freesurfer-cross-sectional /homedtic/gmarti/DATA/Data/ADNI_BIDS_NOTEMPTY/ /homedtic/gmarti/DATA/Data/ADNI_FREE/ -tsv /homedtic/gmarti/DATA/Data/participants_small.tsv -np 4
# clinica run t1-freesurfer-cross-sectional /homedtic/gmarti/DATA/Data/ADNI_BIDS_NOTEMPTY/ /homedtic/gmarti/DATA/Data/ADNI_FREE/ -tsv /homedtic/gmarti/DATA/Data/participants_small.tsv
# do some work
duration=$SECONDS
echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
