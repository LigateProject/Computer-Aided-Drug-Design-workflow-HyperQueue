import dataclasses
import logging
import os
from pathlib import Path
from typing import Optional

from ....utils.io import ensure_directory, iterate_files
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class AWHParams:
    diffusion: float = 0.005
    replicates: int = 3
    cores: int = 8


def find_latest_checkpoint(checkpoint_dir: Path) -> Optional[Path]:
    """
    Return the checkpoint from the given `checkpoint_dir` that was modified most recently.
    """
    files = list(iterate_files(checkpoint_dir, lambda p: p.suffix == ".cpt"))
    files = sorted(files, key=lambda p: os.stat(p).st_mtime)
    if len(files) > 0:
        return files[-1]
    return None

"""
for each edge:
    for each pose:
        runAWH



"""

@trace_fn()
def run_awh_until_convergence(params: AWHParams, directory: Path, gmx: Gromacs):
    logger.info(f"Running AWH at {directory} with params {params}")

    checkpoint_dir = directory / "cpt_complex"
    existing_checkpoint: Optional[Path] = None

    if checkpoint_dir.is_dir():
        # Restoring computation
        existing_checkpoint = find_latest_checkpoint(checkpoint_dir)
        logger.info(f"Restoring AWH checkpoint from {existing_checkpoint}")

        """
        A checkpoint file is needed to restart an AWH simulation that was interrupted to calculate the RBFE estimate.
        Given the frequency at which RBFE estimates are calculated and the performance to be expected for a simulation of a protein-hybrid ligand complex, a new checkpoint file should be written every 5 min.
        TO REPRODUCE REFERENCE DATA: set -cpt 2
        TODO: turn the time interval after which checkpoint files are written (currently set to 5 min: -cpt 5) into a user parameter because it is coupled to the frequency at which free energy estimates are calculated
        """
    else:
        # Fresh computation
        checkpoint_dir = ensure_directory(checkpoint_dir)

    args = [
        "mdrun",
        "-deffnm", "production_complex",
        "-cpnum",
        "-cpt", "5",
        "-cpo", f"{checkpoint_dir.name}/state",
        "-pin", "on",
        "-ntmpi", "1",
        "-ntomp", str(params.cores),
        "-nb", "gpu",
        # Try below parameters on the CPU
        "-pme", "gpu",
        "-pmefft", "gpu",
        "-bonded", "gpu",
        "-update", "cpu"
    ]
    if existing_checkpoint is not None:
        args.extend([
            "-cpi", existing_checkpoint.relative_to(directory)
        ])
    gmx.execute(args, workdir=directory)
