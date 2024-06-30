#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> ./stage.sh <build-dir> <install-dir>

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

cd "${BUILD_DIR}"

STAGE_DIR=stage

if [ ! -d "${STAGE_DIR}" ] ; then
  echo "Downloading Stage"
  git clone https://gitlab.com/gromacs/stage.git --depth=1 "${STAGE_DIR}"
fi

STAGE_INSTALL_DIR=${INSTALL_DIR}/stage

echo "Building Stage"
mkdir -p "${STAGE_DIR}"/build
cd "${STAGE_DIR}"/build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_DOCS=OFF \
      ..

make -j "${BUILD_THREADS}"

mkdir -p "${STAGE_INSTALL_DIR}"
cp -r ./* "${STAGE_INSTALL_DIR}"/

# Save the Promod Python, library and binary directories into the environment script
echo "# Stage" >> "$ENVIRONMENT_SCRIPT"
echo 'export PATH=${PATH}:'"${STAGE_INSTALL_DIR}/bin" >> "$ENVIRONMENT_SCRIPT"
