FROM ubuntu:21.04

# General dependencies
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && \
    apt-get install -y wget git build-essential cmake python3-pip pkg-config

WORKDIR /deps

# Install Gromacs
COPY deps/gromacs-2023.1.sh scripts/
RUN ./scripts/install-gromacs.sh build /usr/local

# Install Stage
COPY deps/stage.sh scripts/
RUN ./scripts/install-stage.sh build
