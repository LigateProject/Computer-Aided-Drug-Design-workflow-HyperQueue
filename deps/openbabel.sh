#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> OPENBABEL_VERSION=3.1.1 ./openbabel.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
OPENBABEL_VERSION=${OPENBABEL_VERSION:-3.1.1}
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

cd "${BUILD_DIR}"

OPENBABEL_DIR=openbabel-"${OPENBABEL_VERSION}"

ARCHIVE_NAME="${OPENBABEL_DIR}".tar.gz

if [ ! -f "${ARCHIVE_NAME}" ] ; then
  echo "Downloading OpenBabel ${OPENBABEL_VERSION}"
  TAG="${OPENBABEL_VERSION//./-}"
  wget https://github.com/openbabel/openbabel/archive/refs/tags/openbabel-"${TAG}".tar.gz -O "${ARCHIVE_NAME}"
  mkdir -p "${OPENBABEL_DIR}"
  tar -xf "${ARCHIVE_NAME}" -C "${OPENBABEL_DIR}" --strip-components=1
fi

OPENBABEL_INSTALL_DIR=${INSTALL_DIR}/openbabel

echo "Building OpenBabel ${OPENBABEL_VERSION}"
mkdir -p "${OPENBABEL_DIR}"/build
cd "${OPENBABEL_DIR}"/build
cmake .. -DCMAKE_INSTALL_PREFIX="${OPENBABEL_INSTALL_DIR}" \
         -DRUN_SWIG=ON \
         -DPYTHON_BINDINGS=ON \
         -DMINIMAL_BUILD=OFF \
         -DBUILD_GUI=OFF \
         -DBOOST_ROOT="${INSTALL_DIR}"/boost
make -j "${BUILD_THREADS}"
make install

# Save the Openbabel binary directory into the environment script
OPENBABEL_BIN_DIR=$(realpath "${OPENBABEL_INSTALL_DIR}"/bin)
echo "# OpenBabel" >> "$ENVIRONMENT_SCRIPT"
echo 'export PATH=${PATH}:'"${OPENBABEL_BIN_DIR}" >> "$ENVIRONMENT_SCRIPT"
