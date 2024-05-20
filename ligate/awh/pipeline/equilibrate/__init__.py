import dataclasses
import logging
from pathlib import Path

from ....utils.io import copy_files
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class EquilibrateParams:
    file: Path
    workdir: Path
    cores: int
    steps: int = 100


def equilibrate(params: EquilibrateParams, gmx: Gromacs):
    assert params.file.is_file()

    logging.info(f"Performing equilibrate with {params}")

    mpi_procs = 1
    omp_procs = params.cores
    args = [
        "-pin",
        "on",
        "-ntmpi",
        str(mpi_procs),
        "-ntomp",
        str(omp_procs),   
    ]

    filename = params.file.stem
    copy_files([params.file], params.workdir)
    gmx.execute(["mdrun", *args, "-deffnm", filename], workdir=params.workdir)
