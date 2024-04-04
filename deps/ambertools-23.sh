#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> ./ambertools-23.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

CURRENT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
AMBERTOOLS_ARCHIVE="${CURRENT_DIR}/AmberTools23.tar.bz2"

if [ ! -f "${AMBERTOOLS_ARCHIVE}" ] ; then
  echo "Please download AmberTools23 from https://ambermd.org/GetAmber.php#ambertools and put it into the deps directory."
  exit 1
fi

cd "${BUILD_DIR}"
AMBER_DIR="amber-23"

if [ ! -f "${AMBER_DIR}/.extracted" ] ; then
  mkdir -p "${AMBER_DIR}"
  echo "Extracting AmberTools 23"
  tar -xf "${AMBERTOOLS_ARCHIVE}" --strip-components=1 -C"${AMBER_DIR}"
  touch "${AMBER_DIR}/.extracted"
fi

AMBERTOOLS_INSTALL_DIR=${INSTALL_DIR}/ambertools

echo "Building AmberTools 23"
mkdir -p "${AMBER_DIR}"/build
cd "${AMBER_DIR}"/build

# TODO: enable GPU
cmake .. \
      -DCMAKE_INSTALL_PREFIX="${AMBERTOOLS_INSTALL_DIR}" \
      -DCOMPILER=GNU \
      -DMPI=TRUE \
      -DOPENMP=TRUE \
      -DCUDA=FALSE \
      -DINSTALL_TESTS=FALSE \
      -DDOWNLOAD_MINICONDA=FALSE \
      -DBUILD_PYTHON=FALSE \
      -DFORCE_EXTERNAL_LIBS=boost \
      -DBOOST_ROOT="${INSTALL_DIR}"/boost

make -j "${BUILD_THREADS}"
make install

echo "# Ambertools" >> "$ENVIRONMENT_SCRIPT"
echo 'source '"${AMBERTOOLS_INSTALL_DIR}"'/amber.sh' >> "$ENVIRONMENT_SCRIPT"
