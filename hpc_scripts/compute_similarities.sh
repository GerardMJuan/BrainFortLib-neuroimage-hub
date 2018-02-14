#!/bin/bash
#SBATCH -J similar_old
#SBATCH -p default
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o similar_%J.out # STDOUT
#SBATCH -e similar_%J.err # STDERR

module load Python/2.7.12-foss-2017a
python -u compute_similarities.py --in_dir /homedtic/gmarti/DATA/Data/baseline_Syn1_masked/ --in_suffix .nii.gz --method NormalizedCorrelation /homedtic/gmarti/DATA/Data/temporalfile_newbaseline/ --out_file /homedtic/gmarti/DATA/Data/NewBaselineCorrO1.dat
