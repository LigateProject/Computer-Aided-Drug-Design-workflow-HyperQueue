import dataclasses

from hyperqueue.job import Job

from .common import LigandOrProtein, LopWorkload, get_topname, topology_path
from .solvate_minimize import MinimizationOutput
from ..ctx import Context
from ..input import ComputationTriple
from ..mdp import render_mdp


@dataclasses.dataclass
class EquilibrateParams:
    steps: int = 100


def equilibrate_task(ctx: Context, workload: LopWorkload, triple: ComputationTriple,
                     params: EquilibrateParams):
    equi_dir = workload.directory / "equi_NVT"
    equi_dir.mkdir(parents=True, exist_ok=True)

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
                minimization_output: MinimizationOutput, job: Job):
    ligand_workload = LopWorkload(lop=LigandOrProtein.Ligand,
                                  directory=minimization_output.ligand_directory)
    protein_workload = LopWorkload(lop=LigandOrProtein.Protein,
                                   directory=minimization_output.protein_directory)

    job.function(equilibrate_task, args=(ctx, ligand_workload, triple, params),
                 deps=[minimization_output.ligand_task], name="equilibrate-ligand")
    job.function(equilibrate_task, args=(ctx, protein_workload, triple, params),
                 deps=[minimization_output.protein_task], name="equilibrate-protein")
