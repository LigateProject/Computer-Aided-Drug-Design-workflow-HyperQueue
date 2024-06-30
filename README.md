# Ligate Ligen/Gromacs CADD workflow
This repository contains a HyperQueue workflow that implements a LiGen virtual screening + docking pipeline, and also a
CADD pipeline that adds integration with GROMACS.

Both pipelines use [HyperQueue](https://it4innovations.github.io/hyperqueue) to build and execute a task graph.

## Installation

There are several external dependencies required to run the workflows. They can be installed in two ways, with a Dockerfile or natively on the target system.

Before installing the dependencies, you have to download `AmbertTools23.tar.bz` from https://ambermd.org/GetAmber.php (registration is required to download it), and put it into the `deps` directory.

To use the Python packages, you should have Python 3.10 or 3.11.

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

Steps 3) - 5) are only needed for the CADD pipeline.

1) Create a virtual environment
    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    (venv) $ python3 -m pip install -U setuptools wheel pip 
    (venv) $ python3 -m pip install uv
    ```
2) Install Python dependencies
    ```bash
    (venv) $ uv pip sync requirements.txt
    ```
3) Install native dependencies
   ```bash
   (venv) $ python3 env.py install
   ```
   - The installation step will generate an `env.sh` file, which you should load before using this
   package (and before executing the `check-env` command):
   ```bash
   (venv) $ source env.sh
   ```
   - You can also run the scripts in the `deps` directory manualy, in the same order as in the [Dockerfile](Dockerfile).
4) Check if everything has been installed correctly
   ```bash
   (venv) $ python3 main.py check-env
   ```
