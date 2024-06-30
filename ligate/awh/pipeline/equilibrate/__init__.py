import dataclasses
from pathlib import Path

from ...common import ComplexOrLigand
from ...scripts import PREPARE_EQUILIBRATION_SCRIPT, SCRIPTS_DIR
from ....mdp import generate_eq_nvt_l0_mdp
from ....utils.cmd import execute_command, replace_env
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class EquilibrateParams:
    steps: int
    cores: int


@trace_fn()
def prepare_equilibrate(directory: Path, params: EquilibrateParams, gmx: Gromacs):
    with generate_eq_nvt_l0_mdp(params.steps) as mdp:
        env = replace_env(
            OMP_NUM_THREADS=str(params.cores),
            CADD_SCRIPTS_DIR=str(SCRIPTS_DIR),
            GROMACS=str(gmx.binary_path),
            MDP_FILE=str(mdp)
        )

        execute_command(
            [PREPARE_EQUILIBRATION_SCRIPT],
            workdir=directory,
            env=env
        )


@trace_fn()
def equilibrate(input: ComplexOrLigand, params: EquilibrateParams, gmx: Gromacs):
    result = gmx.execute([
        "mdrun",
        "-pin", "on",
        "-ntmpi", "1",
        "-ntomp", params.cores,
        "-deffnm", input.equiNVT.stem
    ], workdir=input.path, check=False)
    if result.returncode == 0:
        print("EQUILIBRATION SUCCEEDED")
    else:
        print(f"EQUILIBRATION FAILED: {result.returncode}")
