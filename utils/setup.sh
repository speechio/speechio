#!/usr/bin/env bash

export WENET_ROOT=/home/speechio/work/wenet

export CUDA_VERSION=10.2
export PYTHON_VERSION=3.9
export PYTORCH_VERSION=1.9

## Create & Activate virtual env 
conda create -n speechio python=$PYTHON_VERSION
#conda activate speechio || exit 1

## CUDA
#conda install -c nvidia cudatoolkit=$CUDA_VERSION

##
pip3 install -r .requirements.txt

## setup wenet python dependency
utils/setup_wenet.sh

## K2, problematic
#conda install -c k2-fsa -c pytorch -c conda-forge k2 cudatoolkit=$CUDA_VERSION python=$PYTHON_VERSION pytorch=$PYTORCH_VERSION

