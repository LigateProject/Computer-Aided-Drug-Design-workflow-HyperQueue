import dataclasses
from pathlib import Path

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from .common import LigandOrProtein, get_topname, topology_path
from .equilibrate import EquilibrateOutput, EquilibratePartOutput
from ..ctx import Context
from ..input import ComputationTriple
from ..mdp import render_mdp


@dataclasses.dataclass
class AWHParams:
    steps: int = 100
    diffusion: float = 0.005
    replicates: int = 3


def awh_task(ctx: Context, lop: LigandOrProtein, workload: EquilibratePartOutput,
             directory: Path, mdp_path: Path, triple: ComputationTriple, params: AWHParams):
    topname = get_topname(lop, triple)
    topology = ctx.workdir / topology_path(topname)

    ctx.gmx.execute([
        "grompp",
        "-f", mdp_path,
        "-c", workload.equi_directory / "equi_NVT.gro",
        "-p", topology,
        "-o", "awh.tpr",
        "-po", "awhout.mdp",
        "-maxwarn", "2"
    ], workdir=directory)

    mpi_procs = 1
    if lop == LigandOrProtein.Protein:
        mpi_procs = 4
    omp_procs = 4  # TODO

    cpt_dir = directory / "cpt"
    cpt_dir.mkdir(parents=True, exist_ok=True)

    ctx.gmx.execute([
        "mdrun",
        "-deffnm", "awh",
        "-cpnum",
        "-cpt", "60",
        "-pin", "on",
        "-cpo", "cpt/state",
        "-ntmpi", str(mpi_procs),
        "-ntomp", str(omp_procs)
    ], workdir=directory,
        env={
            "OMP_NUM_THREADS": str(omp_procs)
        })


def awh(ctx: Context, triple: ComputationTriple, params: AWHParams,
        equilibrate_output: EquilibrateOutput, job: Job):
    generated_mdp = (ctx.workdir / "generated_production.mdp").resolve()
    render_mdp(ctx.mdpdir / "production.mdp", generated_mdp, nsteps=params.steps,
               awh1_dim1_diffusion=params.diffusion)

    def create_tasks(lop: LigandOrProtein, output: EquilibratePartOutput, dependency: Task):
        tasks = []
        for run in range(1, params.replicates + 1):
            run_dir = output.equi_directory / "AWH" / f"run{run}"
            run_dir.mkdir(parents=True, exist_ok=True)
            task = job.function(
                awh_task,
                args=(ctx, lop, output, run_dir, generated_mdp, triple, params),
                deps=[dependency],
                name=f"awh-{'ligand' if lop == LigandOrProtein.Ligand else 'protein'}-{run}",
            )
            tasks.append(task)

    create_tasks(LigandOrProtein.Ligand, equilibrate_output.ligand_output,
                 equilibrate_output.ligand_task)
    create_tasks(LigandOrProtein.Protein, equilibrate_output.protein_output,
                 equilibrate_output.protein_task)
