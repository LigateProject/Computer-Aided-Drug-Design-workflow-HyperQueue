import dataclasses
import os
import subprocess
import tempfile
from pathlib import Path

from ...scripts import CREATE_HYBRID_LIGANDS_SCRIPT, SCRIPTS_DIR
from ....utils.io import copy_directory
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class CreateHybridLigandsParams:
    input_dir: Path
    output_dir: Path
    cores: int


def create_hybrid_ligands(params: CreateHybridLigandsParams, gmx: Gromacs):
    with tempfile.TemporaryDirectory() as dir:
        copy_directory(params.input_dir, dir)
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(params.cores)
        env["CADD_SCRIPTS_DIR"] = str(SCRIPTS_DIR)
        env["GROMACS"] = str(gmx.binary_path)

        subprocess.run(
            CREATE_HYBRID_LIGANDS_SCRIPT,
            check=True,
            cwd=dir,
            env=env
        )
        copy_directory(dir, params.output_dir)
