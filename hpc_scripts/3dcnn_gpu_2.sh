#!/bin/bash
#SBATCH -J c3d
#SBATCH -p high
#SBATCH --workdir=/homedtic/gmarti/LOGS
#SBATCH --gres=gpu:maxwell:1
#SBATCH --mem 60G
#SBATCH -o c3d_%J.out # STDOUT
#SBATCH -e c3d_%j.err # STDERR

source /etc/profile.d/lmod.sh
source /etc/profile.d/easybuild.sh
export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate dlnn
module load CUDA/9.0.176
module load cuDNN/7.0.5-CUDA-9.0.176

python /homedtic/gmarti/CODE/3d-conv-ad/train_c3d_slice.py --config_file /homedtic/gmarti/CODE/3d-conv-ad/configs/config_c3d.ini --output_directory_name c3d
