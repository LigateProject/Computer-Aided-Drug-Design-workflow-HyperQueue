#!/bin/bash

# Usage: ./promod3.sh <build-dir> <install-dir>

set -e

PROMOD_VERSION=3.3
TARGET_DIR=${1:-build}
TARGET_DIR=$(realpath "${TARGET_DIR}")

INSTALL_DIR=${2:-${TARGET_DIR}/promod-${PROMOD_VERSION}/install}

mkdir -p "${TARGET_DIR}"

cd "${TARGET_DIR}"

if [ ! -d "promod-${PROMOD_VERSION}" ] ; then
  git clone https://code.it4i.cz/beranekj/promod3.git --depth=1 --branch ligate-patch promod-${PROMOD_VERSION}
fi

cd promod-${PROMOD_VERSION}

mkdir -p build && cd build

echo "Building Promod3"
# OPTIMIZE has to be kept in sync with OST
cmake -DCMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
      -DOPTIMIZE=ON \
      -DOST_ROOT=<PATH_TO_YOUR_OST_INSTALLATION> \
      -DBOOST_ROOT=<PATH_TO_YOUR_BOOST_INSTALLATION> \
      -DEIGEN3_INCLUDE_DIR=<PATH_TO_YOUR_EIGEN_LIBRARY> \
      -DDISABLE_DOCUMENTATION=ON \
      -DCOMPOUND_LIB=<PATH_TO_compounds.chemlib> \
      ..
# compounds.chemlib is a library for chemical compounds you downloaded as part of the OST installation

make -j "$(nproc)"
make check
make install
