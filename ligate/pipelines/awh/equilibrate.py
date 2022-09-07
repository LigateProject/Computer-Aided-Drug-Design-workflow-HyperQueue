import dataclasses

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from ...mdp import render_mdp
from .ctx import AWHContext
from .common import EQ_NVT_L0_MDP
from .providers import AWHLigandOrProtein, AWHProteinDir
from .solvate_minimize import MinimizationOutput


@dataclasses.dataclass
class EquilibrateParams:
    steps: int = 100


@dataclasses.dataclass
class EquilibrateOutput:
    ligand_task: Task
    protein_task: Task


def equilibrate_task_fn(
    ctx: AWHContext,
    workload: AWHLigandOrProtein,
    params: EquilibrateParams,
):
    generated_mdp = ctx.workdir / "generated_eq_nvt_l0.mdp"
    render_mdp(EQ_NVT_L0_MDP, generated_mdp, nsteps=params.steps)

    ctx.tools.gmx.execute(
        [
            "grompp",
            "-f",
            generated_mdp,
            "-c",
            workload.em_gro,
            "-p",
            workload.get_topology_file(ctx.edge_dir, ctx.protein_forcefield),
            "-o",
            workload.equi_dir.equi_nvt_tpr,
            "-po",
            workload.equi_dir.equi_nvtout_mdp,
            "-maxwarn",
            "2",
        ]
    )

    mpi_procs = 1
    if isinstance(AWHLigandOrProtein, AWHProteinDir):
        mpi_procs = 4
    omp_procs = 4  # TODO

    # TODO: GPU requirements
    ctx.tools.gmx.execute(
        [
            "mdrun",
            "-deffnm",
            "equi_NVT",
            "-pin",
            "on",
            "-ntmpi",
            str(mpi_procs),
            "-ntomp",
            str(omp_procs),
        ],
        workdir=workload.equi_dir.path,
        env={"OMP_NUM_THREADS": str(omp_procs)},
    )


def equilibrate_task(
    job: Job,
    ctx: AWHContext,
    params: EquilibrateParams,
    minimization_output: MinimizationOutput,
) -> EquilibrateOutput:
    def create_task(workload: AWHLigandOrProtein, dependency: Task, name: str) -> Task:
        return job.function(
            equilibrate_task_fn,
            args=(ctx, workload, params),
            deps=[dependency],
            name=name,
        )

    return EquilibrateOutput(
        ligand_task=create_task(
            ctx.edge_dir.ligand_dir,
            minimization_output.ligand_task,
            f"equilibrate-ligand-{ctx.edge_name()}",
        ),
        protein_task=create_task(
            ctx.edge_dir.protein_dir,
            minimization_output.protein_task,
            f"equilibrate-protein-{ctx.edge_name()}",
        ),
    )
