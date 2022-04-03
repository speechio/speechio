#!/bin/bash
git submodule add https://github.com/kpu/kenlm $repo
git submodule update --init --recursive
echo "Done."

