import dataclasses
from pathlib import Path
from typing import Tuple

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from .common import LigandOrProtein, LopWorkload, get_topname, topology_path
from .solvate_minimize import MinimizationOutput
from ..ctx import Context
from ..input import ComputationTriple
from ..mdp import render_mdp


@dataclasses.dataclass
class EquilibrateParams:
    steps: int = 100


@dataclasses.dataclass
class EquilibratePartOutput:
    directory: Path
    equi_directory: Path


@dataclasses.dataclass
class EquilibrateOutput:
    # Tasks are stored separately from the output to avoid passing task references
    # as arguments to downstream tasks.
    ligand_task: Task
    ligand_output: EquilibratePartOutput
    protein_task: Task
    protein_output: EquilibratePartOutput


def equilibrate_task(ctx: Context, workload: LopWorkload, triple: ComputationTriple,
                     equi_dir: Path, params: EquilibrateParams):
    generated_mdp = "generated_eq_nvt_l0.mdp"
    render_mdp(ctx.mdpdir / "eq_nvt_l0.mdp", generated_mdp, nsteps=params.steps)

    ctx.gmx.execute([
        "grompp",
        "-f", generated_mdp,
        "-c", workload.directory / "EM.gro",
        "-p", ctx.workdir / topology_path(get_topname(workload.lop, triple)),
        "-o", equi_dir / "equi_NVT.tpr",
        "-po", equi_dir / "equi_NVTout.mdp",
        "-maxwarn", "2"
    ])

    mpi_procs = 1
    if workload.lop == LigandOrProtein.Protein:
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
                minimization_output: MinimizationOutput, job: Job) -> EquilibrateOutput:
    def create_task(workload: LopWorkload, dependency: Task, name: str) -> Tuple[Task, Path]:
        equi_dir = workload.directory / "equi_NVT"
        equi_dir.mkdir(parents=True, exist_ok=True)
        return (job.function(equilibrate_task, args=(ctx, workload, triple, equi_dir, params),
                             deps=[dependency], name=name), equi_dir)

    ligand_workload = LopWorkload(lop=LigandOrProtein.Ligand,
                                  directory=minimization_output.ligand_directory)
    protein_workload = LopWorkload(lop=LigandOrProtein.Protein,
                                   directory=minimization_output.protein_directory)

    ligand_task, ligand_equi_dir = create_task(ligand_workload, minimization_output.ligand_task,
                                               "equilibrate-ligand")
    protein_task, protein_equi_dir = create_task(protein_workload,
                                                 minimization_output.protein_task,
                                                 "equilibrate-protein")
    return EquilibrateOutput(
        ligand_task=ligand_task,
        ligand_output=EquilibratePartOutput(
            directory=ligand_workload.directory,
            equi_directory=ligand_equi_dir
        ),
        protein_task=protein_task,
        protein_output=EquilibratePartOutput(
            directory=protein_workload.directory,
            equi_directory=protein_equi_dir
        )
    )
