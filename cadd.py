import dataclasses
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import List

import hyperqueue
import typer
from hyperqueue import Client, Job
from hyperqueue.task.function import PythonEnv
from hyperqueue.task.task import Task
from hyperqueue.visualization import visualize_job

from ligate.awh.common import Complex, Ligand
from ligate.awh.ligen.common import LigenTaskContext
# from ligate.awh.pipeline.awh import AWHParams, run_awh_until_convergence
from ligate.awh.pipeline.common import ComplexOrLigandTask, construct_edge_set_from_dir
from ligate.awh.pipeline.docking import (
    DockingPipelineConfig, SubmittedDockingPipeline, hq_submit_ligen_docking_workflow,
)
from ligate.awh.pipeline.equilibrate import EquilibrateParams, prepare_equilibrate
from ligate.awh.pipeline.equilibrate.tasks import hq_submit_equilibrate
from ligate.awh.pipeline.hq import HqCtx
from ligate.awh.pipeline.minimization import MinimizationParams
from ligate.awh.pipeline.minimization.tasks import hq_submit_minimization
from ligate.awh.pipeline.prepare_production_simulation import PrepareProductionSimulationParams
from ligate.awh.pipeline.prepare_production_simulation.tasks import \
    hq_submit_prepare_production_simulation
from ligate.awh.pipeline.select_ligands import LigandSelectionConfig, hq_submit_select_ligands
from ligate.awh.pipeline.virtual_screening import (
    VirtualScreeningPipelineConfig,
    hq_submit_ligen_virtual_screening_workflow,
)
from ligate.utils.io import check_file_exists, delete_path, ensure_directory
from ligate.utils.serde import deserialize_yaml
from ligate.wrapper.gromacs import Gromacs

app = typer.Typer()


@dataclasses.dataclass
class LigenWorkflowData:
    protein_pdb: Path
    probe_mol2: Path
    smi: Path


@dataclasses.dataclass
class LigenWorkfowParams:
    data: LigenWorkflowData
    max_molecules_per_smi: int = 10


def ligen_workflow(
        job: Job,
        params: LigenWorkfowParams,
        ligen_ctx: LigenTaskContext
) -> SubmittedDockingPipeline:
    """
    Checks the input protein, performs virtual screening and docking of the most
    promising ligands.
    """
    ensure_directory(ligen_ctx.workdir)

    # Do not run this for the demo, it is not necessary
    # task = hq_submit_check_protein(params.data.protein_pdb, ligen_ctx.workdir, job)

    # Perform virtual screening. Expand SMI into MOL2, and generate a CSV with scores for each
    # ligand in the input SMI file.
    screening_config = VirtualScreeningPipelineConfig(
        input_smi=params.data.smi,
        input_probe_mol2=params.data.probe_mol2,
        input_protein=params.data.protein_pdb,
        max_molecules_per_smi=params.max_molecules_per_smi,
    )
    output = hq_submit_ligen_virtual_screening_workflow(
        ligen_ctx,
        ligen_ctx.workdir / "vscreening",
        config=screening_config,
        job=job,
        deps=[]
        # deps=[task],
    )

    # Select best N ligands based on the assigned scores, and generate a new SMI file with the
    # best ligands.
    best_ligands_smi = ligen_ctx.workdir / "selected-ligands.smi"
    selection_config = LigandSelectionConfig(
        input_smi=screening_config.input_smi,
        scores_csv=output.output_scores_csv,
        output_smi=best_ligands_smi,
        n_ligands=10,
    )
    select_task = hq_submit_select_ligands(selection_config, job, output.tasks)

    # Dock the best ligands.
    docking_config = DockingPipelineConfig(
        input_smi=best_ligands_smi,
        input_probe_mol2=params.data.probe_mol2,
        input_protein=params.data.protein_pdb,
    )
    return hq_submit_ligen_docking_workflow(
        ligen_ctx, ligen_ctx.workdir / "docking", docking_config, job, deps=[select_task]
    )


def awh_workflow(
        input_dir: Path,
        workdir: Path,
) -> Job:
    gmx = Gromacs("installed/gromacs/bin/gmx")

    reference_dir = ensure_directory("workdir-reference")

    def snapshot_dir(dir: Path, name: str):
        target = reference_dir / name
        if target.is_dir():
            delete_path(target)
        shutil.copytree(dir, reference_dir / name)

    def snapshot_task(job: Job, dir: Path, name: str, tasks: List[Task]) -> Task:
        return job.function(lambda: snapshot_dir(dir, name), deps=tasks, name=f"snapshot-{name}")

    def ref_dir(name: str) -> Path:
        return reference_dir / name

    # Copy the original input directory
    snapshot_dir(input_dir, "after-gromacs-ligen-integration")

    # start_step = "after-gromacs-ligen-integration"
    start_step = "after-hybrid-ligands"
    # start_step = "after-minimization"
    # start_step = "after-prepare-equilibrate"
    # start_step = "after-equilibrate"
    # start_step = "after-prepare-production-simulation"
    actual_input_dir = workdir / "cadd"
    shutil.copytree(ref_dir(start_step), actual_input_dir)

    hq_workdir = workdir / "hq"

    # First job
    # job = create_job(hq_workdir)
    # hq_ctx = HqCtx(job=job)
    # dep = hq_submit_hybrid_ligands(
    #     CreateHybridLigandsParams(directory=actual_input_dir, cores=8),
    #     hq=hq_ctx
    # )
    # snapshot_task(job, actual_input_dir, "after-hybrid-ligands", [dep])
    # run_hq_job(job, local_cluster=True)

    # Second job
    job = create_job(hq_workdir)
    hq_ctx = HqCtx(job=job)

    # Construct the initial task item for a ligand and complex in each pose
    edge_set = construct_edge_set_from_dir(actual_input_dir)
    tasks: List[ComplexOrLigandTask] = []
    for (edge, pose) in edge_set.iterate_poses():
        for item in (Complex, Ligand):
            tasks.append(ComplexOrLigandTask(
                edge=edge,
                pose=pose,
                item=item(edge.pose_dir(pose)),
            ))

    mode = "minimize"

    # Minimization
    if mode == "minimize":
        minimization_params = MinimizationParams(steps=10, cores=4)
        for task in tasks:
            task.task = hq_submit_minimization(task.item, params=minimization_params, gmx=gmx,
                                               hq=hq_ctx.with_dep(task.task))
        dep = snapshot_task(job, actual_input_dir, "after-minimization", [t.task for t in tasks])

        # Prepare equilibration
        equilibrate_params = EquilibrateParams(steps=10, cores=4)
        dep = job.function(
            prepare_equilibrate,
            args=(actual_input_dir, equilibrate_params, gmx),
            name="prepare-equilibrate",
            deps=[dep]
        )
        dep = snapshot_task(job, actual_input_dir, "after-prepare-equilibrate", [dep])

        # Equilibration
        for task in tasks:
            task.task = hq_submit_equilibrate(task.item, params=equilibrate_params, gmx=gmx,
                                              hq=hq_ctx.with_dep(dep))
        dep = snapshot_task(job, actual_input_dir, "after-equilibrate", [t.task for t in tasks])

        # Prepare production simulation
        production_params = PrepareProductionSimulationParams(steps=50)
        for task in tasks:
            task.task = hq_submit_prepare_production_simulation(
                task.item, params=production_params, gmx=gmx,
                hq=hq_ctx.with_dep(dep))
        dep = snapshot_task(job, actual_input_dir, "after-prepare-production-simulation",
                            [t.task for t in tasks])
    elif mode == "awh":
        awh_params = AWHParams(
            cores=8
        )
        dep = snapshot_task(actual_input_dir, "after-prepare-production-simulation", [dep])
        # awh_params = AWHParams(
        #     cores=8
        # )
        # for (edge, pose) in edge_set.iterate_poses():
            #     run_awh_until_convergence(awh_params, edge.pose_dir(pose), gmx=gmx)
            # dep = job.function(run_awh_until_convergence,
            #                    args=(awh_params, edge.pose_dir(pose), gmx),
            #                    resources=ResourceRequest(cpus=awh_params.cores),
            #                    deps=[dep])
            # dep = snapshot_task(actual_input_dir, "after-awh", [dep])
            # break
    else:
        assert False
    return job


def load_ligen_params(path: Path) -> LigenWorkfowParams:
    params = deserialize_yaml(LigenWorkfowParams, path)
    check_file_exists(params.data.protein_pdb)
    check_file_exists(params.data.probe_mol2)
    check_file_exists(params.data.smi)
    return LigenWorkfowParams(
        data=LigenWorkflowData(
            protein_pdb=params.data.protein_pdb.resolve(),
            probe_mol2=params.data.probe_mol2.resolve(),
            smi=params.data.smi.resolve(),
        ),
        max_molecules_per_smi=params.max_molecules_per_smi
    )


def run_hq_job(job: Job, local_cluster: bool = False):
    env = PythonEnv(
        prologue=f"""export PYTHONPATH=$PYTHONPATH:{os.getcwd()}""",
        python_bin=sys.executable
    )

    def run(client: Client):
        submitted = client.submit(job)
        client.wait_for_jobs([submitted])

    if local_cluster:
        with hyperqueue.cluster.LocalCluster() as cluster:
            cluster.start_worker()
            client = cluster.client(python_env=env)
            run(client)
    else:
        run(Client(server_dir=os.environ.get("HQ_SERVER_DIR"), python_env=env))


def create_job(workdir) -> Job:
    return Job(default_workdir=workdir, default_env=dict(HQ_PYLOG="DEBUG"))


@app.command()
def ligen(
        workdir: Path,
        params: Path,
        ligen_container: Path,
        local_cluster: bool = False
):
    workdir = ensure_directory(workdir, clear=True)
    job = create_job(workdir / "hq")

    ligen_ctx = LigenTaskContext(
        workdir=workdir,
        container_path=ligen_container.resolve()
    )
    params = load_ligen_params(params)

    ligen_workflow(
        job,
        params=params,
        ligen_ctx=ligen_ctx
    )

    visualize_job(job, "job.dot")

    run_hq_job(job, local_cluster=local_cluster)


@app.command()
def awh():
    workdir = ensure_directory(Path("workdir"), clear=True)

    job = awh_workflow(Path(
        "backup/ligate-workflows/referenceData/02_refOut_GROMACS_LiGen_integration").resolve(),
                       workdir)
    # awh_workflow(job, Path("data/mcl1/02_refOut_GROMACS_LiGen_integration").absolute(), workdir)
    # awh_workflow(job, Path(
    #     "backup/ligate-workflows/referenceData-mcl1/03_refOut_createHybridLigands").resolve(),
    #              workdir)

    visualize_job(job, "job.dot")

    run_hq_job(job, local_cluster=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    app()
