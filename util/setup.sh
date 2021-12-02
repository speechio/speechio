#!/usr/bin/env bash

KALDI_ROOT=/home/speechio/work/kaldi
WENET_ROOT=/home/speechio/work/wenet

CUDA_VERSION=10.2
PYTHON_VERSION=3.9
PYTORCH_VERSION=1.9

## Create & Activate virtual env 
conda create -n speechio python=$PYTHON_VERSION
#conda activate speechio || exit 1

## CUDA
#conda install -c nvidia cudatoolkit=$CUDA_VERSION

##
pip3 install -r requirements.txt

## K2, problematic
#conda install -c k2-fsa -c pytorch -c conda-forge k2 cudatoolkit=$CUDA_VERSION python=$PYTHON_VERSION pytorch=$PYTORCH_VERSION

## KenLM
#pip3 install https://github.com/kpu/kenlm/archive/master.zip

cd ops/
ln -s $WENET_ROOT/wenet wenet
ln -s $KALDI_ROOT kaldi
cd -
