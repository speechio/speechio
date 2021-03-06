#!/usr/bin/env bash

export PYTHON_VERSION=3.9
export PYTORCH_VERSION=1.9

conda create -n speechio python=$PYTHON_VERSION
conda activate speechio || exit 1

pip3 install numpy
pip3 install torch
pip3 install torchaudio
pip3 install sentencepiece 
pip3 install omegaconf
pip3 install typeguard

## K2, problematic
#conda install -c k2-fsa -c pytorch -c conda-forge k2 cudatoolkit=$CUDA_VERSION python=$PYTHON_VERSION pytorch=$PYTORCH_VERSION

