#!/bin/bash

# Usage: ./gromacs-2023.2.sh <build-dir> <install-dir>

set -e

GROMACS_VERSION=gromacs-2023.2
TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

INSTALL_DIR=${2:-${TARGET_DIR}/${GROMACS_VERSION}/install}

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

if [ ! -f "${GROMACS_VERSION}.tar.gz" ] ; then
  echo "Downloading GROMACS"
  wget https://ftp.gromacs.org/gromacs/${GROMACS_VERSION}.tar.gz
fi
echo "Unzipping GROMACS"
tar -xvf ${GROMACS_VERSION}.tar.gz

cd ${GROMACS_VERSION}

echo "Building GROMACS"
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
  -DGMX_BUILD_OWN_FFTW=ON \
  -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
  ..
make -j "$(nproc)"
make install
