#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> PROMOD_VERSION=3.3.0 ./promod.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
PROMOD_VERSION=${PROMOD_VERSION:-3.3.0}
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

cd "${BUILD_DIR}"

PROMOD_DIR=promod-"${PROMOD_VERSION}"

if [ ! -d "${PROMOD_DIR}" ] ; then
  echo "Downloading Promod ${PROMOD_VERSION}"
  git clone https://git.scicore.unibas.ch/schwede/ProMod3.git --depth=1 --branch "${PROMOD_VERSION}" "${PROMOD_DIR}"
fi

PROMOD_INSTALL_DIR=${INSTALL_DIR}/promod
OST_INSTALL_DIR=${INSTALL_DIR}/ost
BOOST_INSTALL_DIR=${INSTALL_DIR}/boost

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}:${OST_INSTALL_DIR}/lib64
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${INSTALL_DIR}/boost/lib
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${INSTALL_DIR}/openmm/lib

echo "Building Promod ${PROMOD_VERSION}"
# OPTIMIZE has to be kept in sync with OST
mkdir -p "${PROMOD_DIR}"/build
cd "${PROMOD_DIR}"/build
cmake .. -DCMAKE_INSTALL_PREFIX="${PROMOD_INSTALL_DIR}" \
         -DOPTIMIZE=ON \
         -DOST_ROOT="${OST_INSTALL_DIR}" \
         -DBOOST_ROOT="${BOOST_INSTALL_DIR}" \
         -DDISABLE_DOCUMENTATION=ON \
         -DCOMPOUND_LIB="${OST_INSTALL_DIR}"/compounds.chemlib \
         -DPython_EXECUTABLE="$(which python)" \
         -DPython_FIND_VIRTUALENV=ONLY

# compounds.chemlib is a library for chemical compounds that is built as part of OST installation

make -j "${BUILD_THREADS}"
make install

# Save the Promod Python, library and binary directories into the environment script
PROMOD_LIB_DIR=$(realpath "${PROMOD_INSTALL_DIR}"/lib64)
PROMOD_PYTHON_DIR=$(realpath "${PROMOD_LIB_DIR}"/python*/site-packages)
PROMOD_BIN_DIR=$(realpath "${PROMOD_INSTALL_DIR}"/bin)
echo "# Promod" >> "$ENVIRONMENT_SCRIPT"
echo 'export PYTHONPATH=${PYTHONPATH}:'"${PROMOD_PYTHON_DIR}" >> "$ENVIRONMENT_SCRIPT"
echo 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:'"${PROMOD_LIB_DIR}" >> "$ENVIRONMENT_SCRIPT"
echo 'export PATH=${PATH}:'"${PROMOD_BIN_DIR}" >> "$ENVIRONMENT_SCRIPT"
