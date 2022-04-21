#!/usr/bin/env bash

if [ $# -ne 1 ]; then
    echo "setup_kenlm.sh dir"
    exit 1;
fi

dir=$1

git clone --depth 1 https://github.com/kpu/kenlm $dir

mkdir -p $dir/build && cd $dir/build
cmake ..
make -j 4
cd -

echo "KenLM tools have been installed to: $dir/build/bin, please add it to your PATH"

