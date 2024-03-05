#!/bin/bash

# Usage: OPENMM_VERSION=7.7.0 ./openmm.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
OPENMM_VERSION=${OPENMM_VERSION:-7.7.0}
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

cd "${BUILD_DIR}"

OPENMM_DIR=openmm-"${OPENMM_VERSION}"
ARCHIVE_NAME="${OPENMM_DIR}".tar.gz

if [ ! -f "${ARCHIVE_NAME}" ] ; then
  echo "Downloading OpenMM ${OPENMM_VERSION}"
  wget https://github.com/openmm/openmm/archive/refs/tags/"${OPENMM_VERSION}".tar.gz -O "${ARCHIVE_NAME}"
fi

echo "Unzipping OpenMM"
mkdir -p "${OPENMM_DIR}"
tar -xf "${ARCHIVE_NAME}" -C "${OPENMM_DIR}" --strip-components=1

echo "Building OpenMM ${OPENMM_VERSION}"

mkdir -p "${OPENMM_DIR}"/build
cd "${OPENMM_DIR}"/build

cmake .. \
  -DCMAKE_INSTALL_PREFIX="${INSTALL_DIR}"/openmm \
  -DOPENMM_BUILD_REFERENCE_TESTS=OFF \
  -DOPENMM_BUILD_EXAMPLES=OFF \
  -DOPENMM_BUILD_OPENCL_LIB=OFF \
  -DBUILD_TESTING=OFF \
  -DOPENMM_BUILD_C_AND_FORTRAN_WRAPPERS=OFF \
  -DOPENMM_BUILD_PYTHON_WRAPPERS=ON && \
make -j"${BUILD_THREADS}" && \
make install

# Needed for the Python build
export OPENMM_INCLUDE_PATH="${INSTALL_DIR}/openmm/include"
export OPENMM_LIB_PATH="${INSTALL_DIR}/openmm/lib"

cd python
python3 setup.py build
python3 setup.py install
