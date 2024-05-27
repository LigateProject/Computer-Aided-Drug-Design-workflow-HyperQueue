import dataclasses
import os
import subprocess
from pathlib import Path

from ...scripts import CREATE_HYBRID_LIGANDS_SCRIPT, SCRIPTS_DIR
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class CreateHybridLigandsParams:
    directory: Path
    cores: int


def create_hybrid_ligands(params: CreateHybridLigandsParams, gmx: Gromacs):
    env = os.environ.copy()
    env["OMP_NUM_THREADS"] = str(params.cores)
    env["CADD_SCRIPTS_DIR"] = str(SCRIPTS_DIR)
    env["GROMACS"] = str(gmx.binary_path)

    subprocess.run(
        CREATE_HYBRID_LIGANDS_SCRIPT,
        check=True,
        cwd=params.directory,
        env=env
    )
