#!/bin/bash
#SBATCH -J substract_baseline
#SBATCH -p short
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH -o sub_b_%J.out # STDOUT
#SBATCH -e sub_b_%j.err # STDERR

module load Python/3.6.4-foss-2017a

python3 substract_baseline.py --in_dir_baseline /homedtic/gmarti/DATA/Data/baseline_Syn2_masked/ --in_dir_followup /homedtic/gmarti/DATA/Data/followups_Syn2_masked/ --out_directory /homedtic/gmarti/DATA/Data/diff_Syn2_masked/ --img_suffix nii.gz --out_suffix diff
