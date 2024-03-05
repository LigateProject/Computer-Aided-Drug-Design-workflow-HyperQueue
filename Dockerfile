FROM ubuntu:22.04

ENV OPENMM_VERSION="7.7.0"
ENV PROMOD_VERSION="3.3.1"
ENV OST_VERSION="2.4.0"
ENV BOOST_VERSION="1.82.0"

ENV DEPS_BUILD_DIR="/deps/build"
ENV DEPS_INSTALL_DIR="/deps/install"
ENV ENVIRONMENT_SCRIPT="/deps/env.sh"

ENV BUILD_THREADS="16"

# Install global dependencies
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        cmake \
        git \
        build-essential \
        g++ \
        wget \
        tar \
        swig \
        doxygen \
        python3-pip

RUN python3 -m pip install -U poetry setuptools wheel pip

RUN mkdir -p ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

WORKDIR ${DEPS_BUILD_DIR}

# Install OpenMM dependencies
RUN python3 -m pip install numpy==1.26.4 cython==3.0.8
RUN apt-get install -y --no-install-recommends libpython3-dev

# Install OpenMM
COPY ./deps/openmm.sh /deps
RUN /deps/openmm.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

ENV OPENMM_INSTALL_DIR="${DEPS_INSTALL_DIR}/openmm"

# Install OST dependencies
RUN apt-get -y install --no-install-recommends \
        libeigen3-dev \
        libsqlite3-dev \
        libpng-dev \
        libfftw3-dev \
        libtiff-dev

# Install Boost (OST dependency)
COPY ./deps/boost.sh /deps
RUN /deps/boost.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

ENV OST_INSTALL_DIR=${DEPS_BUILD_DIR}/ost

# Install OST
COPY ./deps/ost.sh /deps
RUN /deps/ost.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

# Clean up space
# RUN rm -rf ${DEPS_BUILD_DIR}
# RUN rm -rf /var/lib/apt/lists/*
# source /deps/env.sh
