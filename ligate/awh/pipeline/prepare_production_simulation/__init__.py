import dataclasses
from pathlib import Path

from ...scripts import PREPARE_PRODUCTION_SIMULATION_SCRIPT, SCRIPTS_DIR
from ....utils.cmd import execute_command, replace_env
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class PrepareProductionSimulationParams:
    directory: Path
    steps: int = -1
    cores: int = 4


def prepare_production_simulation(params: PrepareProductionSimulationParams, gmx: Gromacs):
    env = replace_env(
        OMP_NUM_THREADS=str(params.cores),
        CADD_SCRIPTS_DIR=str(SCRIPTS_DIR),
        GROMACS=str(gmx.binary_path)
    )

    execute_command(
        [PREPARE_PRODUCTION_SIMULATION_SCRIPT],
        workdir=params.directory,
        env=env
    )
