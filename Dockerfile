FROM ubuntu:21.04

# General dependencies
RUN apt-get update && \
    apt-get install -y wget git build-essential cmake

WORKDIR /deps
COPY scripts scripts

# Install Gromacs
RUN ./scripts/install-gromacs.sh build /usr/local

# Install OpenBabel
RUN ./scripts/install-openbabel.sh build /usr/local
