#!/bin/bash

set -e

COMMIT=ligate
STAGE_VERSION=stage-${COMMIT}
TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

wget https://gitlab.com/kobzol/stage/-/archive/${COMMIT}/${STAGE_VERSION}.tar.gz

tar -xvf ${STAGE_VERSION}.tar.gz

cd ${STAGE_VERSION}

mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_DOCS=OFF ..
make -j "$(nproc)"
