#!/bin/bash

# Usage: ./stage.sh <build-dir>

set -e

TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

if [ ! -d "stage" ] ; then
  git clone https://gitlab.com/gromacs/stage.git
fi

cd stage
git checkout 27140bbd888e49e97beba7b8f75b7f484c766197
mkdir -p build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_DOCS=OFF ..
