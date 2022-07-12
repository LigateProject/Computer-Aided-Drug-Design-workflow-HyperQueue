FROM ubuntu:21.04

# General dependencies
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && \
    apt-get install -y wget git build-essential cmake python3-pip pkg-config

WORKDIR /deps

# Install Gromacs
COPY scripts/install-gromacs.sh scripts/
RUN ./scripts/install-gromacs.sh build /usr/local

# Install OpenBabel
COPY scripts/install-openbabel.sh scripts/
RUN ./scripts/install-openbabel.sh build /usr/local

# Install AcPype
COPY scripts/install-acpype.sh scripts/
RUN ./scripts/install-acpype.sh

# Install Stage
COPY scripts/install-stage.sh scripts/
RUN ./scripts/install-stage.sh build
