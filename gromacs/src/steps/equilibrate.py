import dataclasses
from pathlib import Path
from typing import List

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from .common import LigandOrProtein, get_topname, topology_path
from ..ctx import Context
from ..input import ComputationTriple
from ..mdp import render_mdp


@dataclasses.dataclass
class EquilibrateParams:
    steps: int = 100


@dataclasses.dataclass
class EquilibrateWorkload:
    lop: LigandOrProtein
    directory: Path

    def __repr__(self) -> str:
        return f"{self.lop} at `{str(self.directory)}`"


def equilibrate_task(ctx: Context, input: EquilibrateWorkload, triple: ComputationTriple,
                     params: EquilibrateParams):
    equi_dir = input.directory / "equi_NVT"
    equi_dir.mkdir(parents=True, exist_ok=True)

    generated_mdp = "generated_eq_nvt_l0.mdp"
    render_mdp(ctx.mdpdir / "eq_nvt_l0.mdp", generated_mdp, nsteps=params.steps)

    ctx.gmx.execute([
        "grompp",
        "-f", generated_mdp,
        "-c", input.directory / "EM.gro",
        "-p", ctx.workdir / topology_path(get_topname(input.lop, triple)),
        "-o", equi_dir / "equi_NVT.tpr",
        "-po", equi_dir / "equi_NVTout.mdp",
        "-maxwarn", "2"
    ])

    mpi_procs = 1
    if input.lop == LigandOrProtein.Protein:
        mpi_procs = 4
    omp_procs = 4  # TODO

    # TODO: GPU requirements
    ctx.gmx.execute([
        "mdrun",
        "-deffnm", "equi_NVT",
        "-pin", "on",
        "-ntmpi", str(mpi_procs),
        "-ntomp", str(omp_procs)
    ], workdir=equi_dir,
        env={
            "OMP_NUM_THREADS": str(omp_procs)
        })


def equilibrate(ctx: Context, triple: ComputationTriple, params: EquilibrateParams,
                deps: List[Task], job: Job) -> List[Task]:
    ligand_dir = ctx.workdir / "ligand"
    protein_dir = ctx.workdir / "protein"

    inputs = [
        EquilibrateWorkload(lop=LigandOrProtein.Ligand, directory=ligand_dir),
        EquilibrateWorkload(lop=LigandOrProtein.Protein, directory=protein_dir)
    ]
    return [job.function(equilibrate_task, args=(ctx, input, triple, params), deps=deps)
            for input in inputs]
