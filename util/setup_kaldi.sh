#!/usr/bin/env bash

mkdir -p $KALDI_ROOT/build
cd $KALDI_ROOT/build
MKLROOT=$MKL_ROOT cmake -DMATHLIB=MKL  -DCMAKE_INSTALL_PREFIX=../dist  ..
cmake --build . --target install -- -j40
cd -

cd libsio/deps/
ln -s $KALDI_ROOT/dist kaldi_dist
cd -

