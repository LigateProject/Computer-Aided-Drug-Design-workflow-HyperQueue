import dataclasses
from pathlib import Path

from ...scripts import CREATE_HYBRID_LIGANDS_SCRIPT, SCRIPTS_DIR
from ....utils.cmd import execute_command, replace_env
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class CreateHybridLigandsParams:
    directory: Path
    cores: int


def create_hybrid_ligands(params: CreateHybridLigandsParams, gmx: Gromacs):
    env = replace_env(
        OMP_NUM_THREADS=str(params.cores),
        CADD_SCRIPTS_DIR=str(SCRIPTS_DIR),
        GROMACS=str(gmx.binary_path)
    )

    execute_command(
        [CREATE_HYBRID_LIGANDS_SCRIPT],
        workdir=params.directory,
        env=env
    )
