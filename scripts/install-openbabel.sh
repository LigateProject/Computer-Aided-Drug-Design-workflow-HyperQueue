#!/bin/bash

set -e

TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

OPENBABEL_VERSION=openbabel-2-4-1

INSTALL_DIR=${2:-${TARGET_DIR}/openbabel-${OPENBABEL_VERSION}/install}

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

wget https://github.com/openbabel/openbabel/archive/${OPENBABEL_VERSION}.tar.gz
tar -xvf ${OPENBABEL_VERSION}.tar.gz

cd openbabel-${OPENBABEL_VERSION}

mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
  ..
make -j "$(nproc)"
make install
