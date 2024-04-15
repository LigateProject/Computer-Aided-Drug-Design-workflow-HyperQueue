FROM ubuntu:22.04

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
        libopenmpi-dev \
        python3-pip \
        python3-venv \
        libpython3-dev \
        libeigen3-dev \
        libsqlite3-dev \
        libpng-dev \
        libfftw3-dev \
        libtiff-dev \
        libbz2-dev \
        gfortran \
        flex \
        bison

RUN python3 -m pip install --no-cache -U setuptools wheel pip
RUN python3 -m pip install --no-cache uv

RUN mkdir -p ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

WORKDIR /cadd

# Python dependencies needed for some of the native dependencies
RUN uv pip install --system --no-cache numpy==1.26.4 cython==3.0.8

# Pre-install the dependencies for a more interactive Docker image build
COPY deps/openmm.sh deps/openmm.sh
RUN ./deps/openmm.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}
COPY deps/boost.sh deps/boost.sh
RUN ./deps/boost.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}
COPY deps/ost.sh deps/ost.sh
RUN ./deps/ost.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}
COPY deps/promod.sh deps/promod.sh
RUN ./deps/promod.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}
COPY deps/openbabel.sh deps/openbabel.sh
RUN ./deps/openbabel.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}
COPY deps/gromacs.sh deps/gromacs.sh
RUN ./deps/gromacs.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}
COPY deps/stage.sh deps/stage.sh
RUN ./deps/stage.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

COPY deps/AmberTools23.tar.bz2 deps/AmberTools23.tar.bz2
COPY deps/ambertools.sh deps/ambertools.sh
RUN ./deps/ambertools.sh ${DEPS_BUILD_DIR} ${DEPS_INSTALL_DIR}

# We need to install Poetry outside of the target environment for the project (which in this case
# is just the global interpreter), otherwise it will break.
COPY pyproject.toml pyproject.toml
COPY requirements.txt requirements.txt
COPY ligate ligate
RUN UV_HTTP_TIMEOUT=1000 uv pip sync --system --no-cache requirements.txt

# Finish the installation of the native dependencies
COPY env.py env.py
RUN python3 env.py install ${DEPS_INSTALL_DIR} --build-dir ${DEPS_BUILD_DIR}

# Install the project
RUN bash -c "source ${ENVIRONMENT_SCRIPT} && python3 env.py check-env"

# Clean up space
RUN rm -rf ${DEPS_BUILD_DIR}
RUN rm -rf /var/lib/apt/lists/*
RUN rm -rf python3 -m pip cache purge
