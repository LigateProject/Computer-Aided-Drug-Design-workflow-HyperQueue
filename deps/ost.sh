#!/bin/bash

# Usage: ENVIRONMENT_SCRIPT=<path> OST_VERSION=2.4.0 ./ost.sh <build-dir> <install-dir>

set -eu

# Arguments
BUILD_DIR=${1:-build}
INSTALL_DIR=${2:-installed}

# Environment variables
OST_VERSION=${OST_VERSION:-2.4.0}
BUILD_THREADS=${BUILD_THREADS:-8}

mkdir -p "${BUILD_DIR}"
mkdir -p "${INSTALL_DIR}"

BUILD_DIR=$(realpath "${BUILD_DIR}")
INSTALL_DIR=$(realpath "${INSTALL_DIR}")

cd "${BUILD_DIR}"

OST_DIR=ost-"${OST_VERSION}"

if [ ! -d "${OST_DIR}" ] ; then
  echo "Downloading OST ${OST_VERSION}"
  git clone https://git.scicore.unibas.ch/schwede/openstructure.git --depth=1 --branch "${OST_VERSION}" "${OST_DIR}"
fi

OST_INSTALL_DIR=${INSTALL_DIR}/ost
OPENMM_INSTALL_DIR=${INSTALL_DIR}/openmm

# Install OST
echo "Building OST ${OST_VERSION}"
mkdir -p "${OST_DIR}"/build
cd "${OST_DIR}"/build
cmake .. -DCMAKE_INSTALL_PREFIX="${OST_INSTALL_DIR}" \
         -DOPTIMIZE=ON \
         -DENABLE_INFO=OFF \
         -DENABLE_MM=ON \
         -DOPEN_MM_LIBRARY="${OPENMM_INSTALL_DIR}"/lib/libOpenMM.so \
         -DOPEN_MM_INCLUDE_DIR="${OPENMM_INSTALL_DIR}"/include \
         -DOPEN_MM_PLUGIN_DIR="${OPENMM_INSTALL_DIR}"/lib/plugins \
         -DBOOST_ROOT="${INSTALL_DIR/boost}" \
         -DPython_EXECUTABLE="$(which python)" \
         -DPython_FIND_VIRTUALENV=ONLY

make -j"${BUILD_THREADS}"
make install

OST_LIB_DIR=$(realpath "${OST_INSTALL_DIR}"/lib64)

# Build compound library
echo "Downloading compound library"
if [ ! -f components.cif ] ; then
  wget https://files.wwpdb.org/pub/pdb/data/monomers/components.cif.gz
  gzip -d -f -q components.cif.gz
fi
if [ ! -f aa-variants-v1.cif ] ; then
  wget https://files.wwpdb.org/pub/pdb/data/monomers/aa-variants-v1.cif.gz
  gzip -d -f -q aa-variants-v1.cif.gz
fi
if [ ! -f chem_comp_model.cif ] ; then
  wget https://files.wwpdb.org/pub/pdb/data/component-models/complete/chem_comp_model.cif.gz
  gzip -d -f -q chem_comp_model.cif.gz
fi

export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:-}:${OST_LIB_DIR}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${INSTALL_DIR}/boost/lib

echo "Building compound library"
"${OST_INSTALL_DIR}"/bin/chemdict_tool create components.cif compounds.chemlib
"${OST_INSTALL_DIR}"/bin/chemdict_tool update aa-variants-v1.cif.gz compounds.chemlib pdb
"${OST_INSTALL_DIR}"/bin/chemdict_tool update chem_comp_model.cif.gz compounds.chemlib pdb

cp compounds.chemlib "${OST_INSTALL_DIR}"/compounds.chemlib

# Save the OST Python and library directories into the environment script
OST_PYTHON_DIR=$(realpath "${OST_LIB_DIR}"/python*/site-packages)
echo "# OST" >> "$ENVIRONMENT_SCRIPT"
echo 'export PYTHONPATH=${PYTHONPATH}:'"${OST_PYTHON_DIR}" >> "$ENVIRONMENT_SCRIPT"
echo 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:'"${OST_LIB_DIR}" >> "$ENVIRONMENT_SCRIPT"
