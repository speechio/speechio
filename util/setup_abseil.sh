#!/usr/bin/env bash
git submodule add https://github.com/abseil/abseil-cpp libsio/deps/abseil-cpp
git submodule update --init --recursive

echo "Done."
