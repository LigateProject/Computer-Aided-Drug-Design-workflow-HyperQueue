#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> GROMACS_VERSION=2023.2 ./gromacs.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
GROMACS_VERSION=${GROMACS_VERSION:-2023.2}
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

cd "${BUILD_DIR}"

GROMACS_DIR=gromacs-"${GROMACS_VERSION}"
ARCHIVE_NAME="${GROMACS_DIR}".tar.gz

if [ ! -f "${ARCHIVE_NAME}" ] ; then
  echo "Downloading GROMACS ${GROMACS_VERSION}"
  wget https://ftp.gromacs.org/gromacs/"${ARCHIVE_NAME}" -O "${ARCHIVE_NAME}"

  echo "Unzipping GROMACS"
  mkdir -p "${GROMACS_DIR}"
  tar -xvf "${ARCHIVE_NAME}" -C "${GROMACS_DIR}" --strip-components=1
fi

GROMACS_INSTALL_DIR=${INSTALL_DIR}/gromacs

echo "Building GROMACS ${GROMACS_VERSION}"
mkdir -p "${GROMACS_DIR}/build"
cd "${GROMACS_DIR}/build"

cmake -DCMAKE_BUILD_TYPE=Release \
  -DGMX_BUILD_OWN_FFTW=ON \
  -DCMAKE_INSTALL_PREFIX="${GROMACS_INSTALL_DIR}" \
  ..
make -j "${BUILD_THREADS}"
make install

# Configure the environment
echo "# Gromacs" >> "$ENVIRONMENT_SCRIPT"
echo "source ${GROMACS_INSTALL_DIR}/bin/GMXRC" >> "$ENVIRONMENT_SCRIPT"
echo "export GMXLIB=${GROMACS_INSTALL_DIR}/share/gromacs/top" >> "$ENVIRONMENT_SCRIPT"
