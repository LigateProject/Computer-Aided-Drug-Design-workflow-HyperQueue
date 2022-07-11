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

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
RUN apt-get update && \
    apt-get install -y python3-pip

# Install AcPype
RUN ./scripts/install-acpype.sh
