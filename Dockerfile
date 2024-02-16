FROM ubuntu:22.04

ENV OPENMM_VERSION="7.7.0"
ENV PROMOD_VERSION="3.3.1"

ENV DEPS_SRC_DIR="/deps/src"
ENV DEPS_BUILD_DIR="/deps/build"
ENV BUILD_THREADS="16"

# Install global dependencies
RUN apt-get update -y && \
    apt-get install -y cmake \
    git \
    g++ \
    wget \
    tar \
    swig \
    doxygen \
    python3-pip && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install -U poetry setuptools wheel pip
RUN python3 -m pip install numpy==1.26.4 cython==3.0.8

RUN mkdir -p ${DEPS_SRC_DIR} ${DEPS_BUILD_DIR}

WORKDIR ${DEPS_SRC_DIR}

# Download OpenMM
RUN wget https://github.com/openmm/openmm/archive/refs/tags/${OPENMM_VERSION}.tar.gz && \
    mkdir openmm-${OPENMM_VERSION} && \
    tar xf ${OPENMM_VERSION}.tar.gz -C openmm-${OPENMM_VERSION} --strip-components=1 && \
    rm ${OPENMM_VERSION}.tar.gz

# Build OpenMM
RUN mkdir -p ${DEPS_SRC_DIR}/openmm-${OPENMM_VERSION}/build && \
    cd ${DEPS_SRC_DIR}/openmm-${OPENMM_VERSION}/build && \
    cmake .. \
      -DCMAKE_INSTALL_PREFIX=${DEPS_BUILD_DIR}/openmm \
      -DOPENMM_BUILD_REFERENCE_TESTS=OFF \
      -DOPENMM_BUILD_EXAMPLES=OFF \
      -DOPENMM_BUILD_OPENCL_LIB=OFF \
      -DBUILD_TESTING=OFF \
      -DOPENMM_BUILD_C_AND_FORTRAN_WRAPPERS=OFF \
      -DOPENMM_BUILD_PYTHON_WRAPPERS=ON && \
    make -j${BUILD_THREADS} && \
    make install

ENV OPENMM_INCLUDE_PATH="${DEPS_BUILD_DIR}/openmm/include"
ENV OPENMM_LIB_PATH="${DEPS_BUILD_DIR}/openmm/lib"

RUN cd ${DEPS_SRC_DIR}/openmm-${OPENMM_VERSION}/build/python && \
    python3 setup.py build && python3 setup.py install

# Delete all sources
RUN rm -rf ${DEPS_SRC_DIR}
