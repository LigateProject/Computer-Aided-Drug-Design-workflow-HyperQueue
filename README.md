# Ligate Ligen/Gromacs CADD workflow
This repository contains various utility functions for converting Ligen/Gromacs files and primarily
it implements two pipelines:
1) Conversion from Ligen data to Gromacs data (`ligconv`)
2) AWH pipeline (`awh`)

Both pipelines use [HyperQueue](https://it4innovations.github.io/hyperqueue) to build and execute
a task graph.

## Installation

There is a bunch of external dependencies required to run the workflow. They can be installed in two ways, with a Dockerfile or natively on the target system.

### Docker installation
Install Docker and run:
```bash
$ docker build -t cadd .
```
You can convert the resulting image to Singularity/Apptainer if you need to execute it on an HPC
cluster.

### Native installation

Before starting to set up anything, you should have at least the following packages available:

- C/C++ compiler
- CMake
- CPython development headers (`python-dev`)
- MPI implementation (for compiling `mpi4py`)
    - Preferably OpenMPI, AmberTools seems to have some issue with MPICH
    - For example `libopenmpi-dev`

You will then need to install several dependencies. You can examine the [Dockerfile](Dockerfile) to see how it installs these dependencies on Ubuntu 22.04.

1) Create a virtual environment
    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv) $ python3 -m pip install -U setuptools wheel pip 
    ```
2) Install `pipx` so that you can run Poetry
    ```bash
    (venv) $ python3 -m pip pipx 
    ```
3) Install Python dependencies
    ```bash
    (venv) $ pipx run poetry install --extras awh
    ```
4) Install native dependencies
   ```bash
   (venv) $ python3 env.py install
   ```
   - The installation step will generate an `env.sh` file, which you should load before using this
   package (and before executing the `check-env` command):
   ```bash
   (venv) $ source awh-env.sh
   ```
   - You can also run the scripts in the `deps` directory manualy, in the same order as in the Dockerfile.
5) Check if everything has been installed correctly
   ```bash
   (venv) $ python3 main.py check-env
   ```
