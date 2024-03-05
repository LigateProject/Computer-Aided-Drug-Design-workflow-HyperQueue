#!/bin/bash

# Usage: ./stage.sh <build-dir>

set -eu

TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

if [ ! -d "stage" ] ; then
  git clone https://gitlab.com/gromacs/stage.git
fi

cd stage
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_DOCS=OFF \
      ..
