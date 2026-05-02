#!/bin/bash
#SBATCH --job-name=unet_train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/user/work/eg23555/fickle/logs/%j.out
#SBATCH --error=/user/work/eg23555/fickle/logs/%j.err
#SBATCH --account=coms038604

module load apps/pytorch/2.5.1-gpu

pip install segmentation-models-pytorch torchmetrics --user --quiet

cd /user/work/eg23555/fickle

python train.py