#!/bin/bash

# Usage: ./ambertools-21.sh <build-dir> <install-dir>
# Requires: MPI, CUDA, Boost

set -e

TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

AMBER_DIR_NAME=amber22_src
INSTALL_DIR=${2:-${TARGET_DIR}/${AMBER_DIR_NAME}/install}

CURRENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
AMBERTOOLS_ARCHIVE="${CURRENT_DIR}/AmberTools23.tar.bz2"

mkdir -p "${TARGET_DIR}"
cd "${TARGET_DIR}"

if [ ! -f "${AMBERTOOLS_ARCHIVE}" ] ; then
  echo "Please download AmberTools23 from https://ambermd.org/GetAmber.php#ambertools and put it into the deps directory."
  exit 1
fi

if [ ! -d "${AMBER_DIR_NAME}" ] ; then
  tar -xvf "${AMBERTOOLS_ARCHIVE}"
fi
cd "${AMBER_DIR_NAME}"

mkdir -p buildToolsForStage && cd buildToolsForStage

cmake .. \
      -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}" \
      -DCOMPILER=GNU \
      -DMPI=TRUE \
      -DOPENMP=TRUE \
      -DCUDA=TRUE \
      -DINSTALL_TESTS=FALSE \
      -DDOWNLOAD_MINICONDA=FALSE \
      -DBUILD_PYTHON=FALSE \
      -DFORCE_EXTERNAL_LIBS=boost

make -j "$(nproc)"
make install
