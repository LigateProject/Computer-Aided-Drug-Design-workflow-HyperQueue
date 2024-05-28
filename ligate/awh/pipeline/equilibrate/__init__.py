import dataclasses
from pathlib import Path

from ...common import ComplexOrLigand
from ...scripts import PREPARE_EQUILIBRATION_SCRIPT, SCRIPTS_DIR
from ....utils.cmd import execute_command, replace_env
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class EquilibrateParams:
    cores: int


@trace_fn()
def equilibrate(input: ComplexOrLigand, params: EquilibrateParams, gmx: Gromacs):
    gmx.execute([
        "mdrun",
        "-pin",
        "on",
        "-ntmpi", "1",
        "-ntomp", params.cores,
        "-deffnm", input.equiNVT.stem
    ], workdir=input.path)


@trace_fn()
def prepare_equilibrate(directory: Path, params: EquilibrateParams, gmx: Gromacs):
    env = replace_env(
        OMP_NUM_THREADS=str(params.cores),
        CADD_SCRIPTS_DIR=str(SCRIPTS_DIR),
        GROMACS=str(gmx.binary_path)
    )

    # TODO: render MDP and pass it to the script
    execute_command(
        [PREPARE_EQUILIBRATION_SCRIPT],
        workdir=directory,
        env=env
    )
