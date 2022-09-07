#!/bin/bash

# Usage: ./install-openbabel.sh <build-dir> <install-dir>

set -e

TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

OPENBABEL_VERSION=ligate

INSTALL_DIR=${2:-${TARGET_DIR}/openbabel-${OPENBABEL_VERSION}/install}

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

wget https://github.com/kobzol/openbabel/archive/${OPENBABEL_VERSION}.tar.gz
tar -xvf ${OPENBABEL_VERSION}.tar.gz

cd openbabel-${OPENBABEL_VERSION}

mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
  -DRUN_SWIG=ON \
  -DPYTHON_BINDINGS=ON \
  -DMINIMAL_BUILD=OFF \
  -DBUILD_GUI=OFF \
  ..
make -j "$(nproc)"
make install
