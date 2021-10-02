#!/usr/bin/env bash

conda activate speechio || exit 1

#conda install -c nvidia cudatoolkit=$CUDA_VERSION
conda install -c anaconda numpy
conda install -c pytorch pytorch=$PYTORCH_VERSION
conda install -c pytorch torchaudio
#conda install -c k2-fsa -c pytorch -c conda-forge k2 cudatoolkit=$CUDA_VERSION python=$PYTHON_VERSION pytorch=$PYTORCH_VERSION

conda install -c conda-forge sentencepiece
conda install -c conda-forge omegaconf

# kenlm python
#pip3 install https://github.com/kpu/kenlm/archive/master.zip
