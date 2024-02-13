import dataclasses
from pathlib import Path
from typing import List

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from .ctx import AWHContext
from .common import PRODUCTION_MDP
from .equilibrate import EquilibrateOutput
from .providers import AWHLigandOrProtein
from ...mdp import render_mdp
from ...utils.io import ensure_directory


@dataclasses.dataclass
class AWHParams:
    steps: int = 100
    diffusion: float = 0.005
    replicates: int = 3


@dataclasses.dataclass
class AWHPartOutput:
    awh_directory: Path
    run_directory: Path
    workload: AWHLigandOrProtein


@dataclasses.dataclass
class AWHPartOutputWithTask:
    output: AWHPartOutput
    task: Task


@dataclasses.dataclass
class AWHOutput:
    outputs: List[AWHPartOutputWithTask]


def awh_task_fn(
    ctx: AWHContext,
    workload: AWHLigandOrProtein,
    run_dir: Path,
    mdp_path: Path,
):
    ctx.tools.gmx.execute(
        [
            "grompp",
            "-f",
            mdp_path,
            "-c",
            workload.equi_dir.equi_nvt_gro,
            "-p",
            workload.get_topology_file(ctx.edge_dir, ctx.protein_forcefield),
            "-o",
            "awh.tpr",
            "-po",
            "awhout.mdp",
            "-maxwarn",
            "2",
        ],
        workdir=run_dir,
    )

    mpi_procs = 1
    if not workload.is_ligand():
        mpi_procs = 4
    omp_procs = 4  # TODO

    cpt_dir = ensure_directory(run_dir / "cpt")
    ctx.tools.gmx.execute(
        [
            "mdrun",
            "-deffnm",
            "awh",
            "-cpnum",
            "-cpt",
            "60",
            "-pin",
            "on",
            "-cpo",
            "cpt/state",
            "-ntmpi",
            str(mpi_procs),
            "-ntomp",
            str(omp_procs),
        ],
        workdir=cpt_dir,
        env={"OMP_NUM_THREADS": str(omp_procs)},
    )


def awh_task(
    job: Job,
    ctx: AWHContext,
    params: AWHParams,
    equilibrate_output: EquilibrateOutput,
) -> AWHOutput:
    generated_mdp = ctx.workdir / "generated_production.mdp"
    render_mdp(
        PRODUCTION_MDP,
        generated_mdp,
        nsteps=params.steps,
        awh_nstout=min(50000, params.steps),
        awh1_dim1_diffusion=params.diffusion,
    )

    def create_tasks(workload: AWHLigandOrProtein, dependency: Task) -> List[AWHPartOutputWithTask]:
        tasks = []
        awh_directory = ensure_directory(workload.equi_dir.path / "AWH")

        for run in range(1, params.replicates + 1):
            run_dir = ensure_directory(awh_directory / f"run{run}")
            task = job.function(
                awh_task_fn,
                args=(ctx, workload, run_dir, generated_mdp),
                deps=[dependency],
                name=f"awh-{'ligand' if workload.is_ligand() else 'protein'}-{run}-{ctx.edge_name()}",
            )
            tasks.append(
                AWHPartOutputWithTask(
                    task=task,
                    output=AWHPartOutput(
                        workload=workload, awh_directory=awh_directory, run_directory=run_dir
                    ),
                )
            )
        return tasks

    outputs = create_tasks(
        ctx.edge_dir.ligand_dir,
        equilibrate_output.ligand_task,
    )
    outputs += create_tasks(
        ctx.edge_dir.protein_dir,
        equilibrate_output.protein_task,
    )
    return AWHOutput(outputs=outputs)
