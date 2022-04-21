#!/usr/bin/env bash

export CUDA_VERSION=10.2
conda install -c nvidia cudatoolkit=$CUDA_VERSION
