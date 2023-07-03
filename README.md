# Ligate Ligen/Gromacs AWH pipeline
This repository contains various utility functions for converting Ligen/Gromacs files and primarily
it implements two pipelines:
1) Conversion from Ligen data to Gromacs data (`ligconv`)
2) AWH pipeline (`awh`)

Both pipelines use [HyperQueue](https://it4innovations.github.io/hyperqueue) to build and execute
a task graph.

## Installation

### Build environment
Before starting to setup anything, you should have at least the following packages available:

- C/C++ compiler
- CMake
- CPython development headers (`python-dev`)
- MPI implementation (for compiling `mpi4py`)
  - Preferably OpenMPI, AmberTools seems to have some issue with MPICH

### External dependencies
- Gromacs 2022
- stage (branch `ligate` from `https://gitlab.com/kobzol/stage`)

The external dependencies can be installed using scripts located
in the `deps` directory, or (preferably) using the `python3 main.py install` command.
There is also a `Dockerfile` which installs all of these dependencies into a Docker image.

### Python dependencies
Python version has to be at least `3.10`.

1) Create a virtual environment
    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ python3 -m pip install -U setuptools wheel pip 
    ```
2) Install `Poetry`
    ```bash
    $ python3 -m pip install poetry 
    ```
3) Install Python dependencies
    ```bash
    $ poetry install 
    ```
4) Install native dependencies
   ```bash
   $ python3 main.py install
   ```
   The installation step will generate a `awh-env.sh` file, which you should load before using this
   package (and before executing the `check-env` command):
   ```bash
   $ source awh-env.sh
   ```

5) Check if everything has been installed correctly
   ```bash
   $ python3 main.py check-env
   ```

## Running the pipeline
```bash
# Conversion from Ligen data to Gromacs compatible data
$ python3 pipeline.py ligconv

# AWH pipeline
$ python3 pipeline.py awh
```
