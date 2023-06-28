# Ligate Ligen/Gromacs AWH pipeline
This repository contains various utility functions for converting Ligen/Gromacs files and primarily
it implements two pipelines:
1) Conversion from Ligen data to Gromacs data (`ligconv`)
2) AWH pipeline (`awh`)

Both pipelines use [HyperQueue](https://it4innovations.github.io/hyperqueue) to build and execute
a task graph.

## Installation

### C packages
- CPython development headers (`python-dev`)
- MPI implementation (for compiling `mpi4py`)

### External dependencies
- Gromacs 2022
- OpenBabel 2.4.1 (branch `ligate` from `https://github.com/kobzol/openbabel`)
- acpype 2022.6.6 (branch `ligate` from `https://github.com/kobzol/acpype`)
- stage (branch `ligate` from `https://gitlab.com/kobzol/stage`)

The external dependencies can be installed using `install-*` scripts located
in the `scripts` directory. There is also a `Dockerfile` which installs all
of these dependencies into a Docker image.

### Python dependencies
Python version has to be `3.11`.

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
3) Python Install dependencies
    ```bash
    $ poetry install 
    ```
4) Download `tmbed` model
   ```bash
   $ tmbed download
   ```

Once you install the dependencies, you also need to set up your environment properly.
If you installed the dependencies globally into your system, it should work automatically. If not,
you can use e.g. something similar to put Gromacs, OpenBabel and Stage files into `PATH` and `PYTHONPATH`:

```bash
# Gromacs
GROMACS_DIR=${PWD}/build/gromacs-2022/install
source "${GROMACS_DIR}"/bin/GMXRC
export GMXLIB=${GMXDATA}/top

# OpenBabel
OPENBABEL_DIR=${PWD}/build/openbabel-ligate/install
export PATH=${PATH}:${OPENBABEL_DIR}/bin
export PYTHONPATH=${PYTHONPATH}:${OPENBABEL_DIR}/lib/python3.10/site-packages/

# Stage
STAGE_DIR=${PWD}/build/stage-ligate/build
export PATH=${PATH}:${STAGE_DIR}/bin
```
The script above sets paths that are used by default by the `install*` scripts. It also assumes
Python `3.10`.

### Environment check
To check whether your environment is set up correctly, run the following command:
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
