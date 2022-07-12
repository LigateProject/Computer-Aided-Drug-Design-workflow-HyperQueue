#!/bin/bash

set -e

GROMACS_VERSION=gromacs-2022
TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

INSTALL_DIR=${2:-${TARGET_DIR}/${GROMACS_VERSION}/install}

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

wget https://ftp.gromacs.org/gromacs/${GROMACS_VERSION}.tar.gz
tar -xvf ${GROMACS_VERSION}.tar.gz

cd ${GROMACS_VERSION}

mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
  -DGMX_BUILD_OWN_FFTW=ON \
  -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
  ..
make -j "$(nproc)"
make install
