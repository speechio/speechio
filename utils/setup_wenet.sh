#!/usr/bin/env bash

export WENET_ROOT=/home/speechio/work/wenet

[ ! -z $WENET_ROOT ] || { echo "need to set WENET_ROOT env variable"; exit 1; }
[ -d $WENET_ROOT ] || { echo "WENET_ROOT dir: $WENET_ROOT doesn't exist"; exit 1; }

cd ops/
ln -s $WENET_ROOT/wenet wenet
cd -

