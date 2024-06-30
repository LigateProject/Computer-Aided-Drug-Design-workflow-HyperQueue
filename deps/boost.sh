#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> BOOST_VERSION=1.82.0 ./boost.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
BOOST_VERSION=${BOOST_VERSION:-1.82.0}
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

cd "${BUILD_DIR}"

BOOST_DIR=boost-"${BOOST_VERSION}"
ARCHIVE_NAME="${BOOST_DIR}".tar.gz

if [ ! -f "${ARCHIVE_NAME}" ] ; then
  echo "Downloading Boost ${BOOST_VERSION}"
  wget https://github.com/boostorg/boost/releases/download/boost-"${BOOST_VERSION}"/boost-"${BOOST_VERSION}".tar.gz -O "${ARCHIVE_NAME}"
fi

echo "Unzipping Boost"
mkdir -p "${BOOST_DIR}"
tar -xf "${ARCHIVE_NAME}" -C "${BOOST_DIR}" --strip-components=1

BOOST_INSTALL_DIR=${INSTALL_DIR}/boost

echo "Building Boost ${BOOST_VERSION}"
cd "${BOOST_DIR}"

# Fix for failing to find pyconfig.h
PYTHON_INCLUDE_DIRS=$(python3 -c "from sysconfig import get_paths as gp; print(gp()['include'])")
export CPLUS_INCLUDE_PATH="${CPLUS_INCLUDE_PATH:-}:${PYTHON_INCLUDE_DIRS}"

./bootstrap.sh --with-python="$(which python3)" --prefix="${BOOST_INSTALL_DIR}"
./b2 install -j"${BUILD_THREADS}" \
  --with-chrono \
  --with-context \
  --with-fiber \
  --with-filesystem \
  --with-iostreams \
  --with-graph \
  --with-program_options \
  --with-python \
  --with-regex \
  --with-system \
  --with-test \
  --with-timer \
  --with-thread

# Save the Boost lib directory into the environment script
BOOST_LIB_DIR=$(realpath "${BOOST_INSTALL_DIR}"/lib)
echo "# Boost" >> "$ENVIRONMENT_SCRIPT"
echo 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:'"${BOOST_LIB_DIR}" >> "$ENVIRONMENT_SCRIPT"
