import multiprocessing
import shutil
from pathlib import Path

import click
from hyperqueue import Job, LocalCluster
from hyperqueue.cluster import WorkerConfig
from hyperqueue.visualization import visualize_job

from ligate.ligconv.common import LigandForcefield, ProteinForcefield
from ligate.pipelines.awh import awh_pipeline
from ligate.pipelines.awh.common import AWHTools
from ligate.pipelines.awh.ctx import AWHContext
from ligate.pipelines.ligconv import LigConvContext, ligconv_pipeline
from ligate.pipelines.ligconv.common import (
    Edge,
    LigConvParameters,
    LigConvTools,
    LigenOutputData,
)
from ligate.pipelines.ligconv.providers import LigConvEdgeDir
from ligate.wrapper.babel import Babel
from ligate.wrapper.gromacs import Gromacs
from ligate.wrapper.stage import Stage

edge = Edge("p38a_2aa", "p38a_2bb")


@click.group()
def cli():
    pass


@cli.command()
def ligconv():
    gmx = Gromacs()
    babel = Babel()
    stage = Stage()

    workdir = Path("experiment/ligconv-hq")
    # shutil.rmtree(workdir, ignore_errors=True)

    ligen_output = LigenOutputData(
        protein_file=Path("ligen/output/p38/protein_amber/protein.pdb"),
        ligand_dir=Path("ligen/output/p38/ligands_gaff2"),
    )
    ligconv_params = LigConvParameters(
        protein_ff=ProteinForcefield.Amber99SB_ILDN,
        ligand_ff=LigandForcefield.Gaff2,
        edges=[edge],
    )

    ligconv_ctx = LigConvContext(
        workdir=workdir,
        params=ligconv_params,
        ligen_data=ligen_output,
        tools=LigConvTools(gmx=gmx, babel=babel, stage=stage),
    )

    job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))

    # Convert outputs from LiGen to GROMACS-compatible inputs
    ligconv_pipeline(job, ligconv_ctx)

    visualize_job(job, "ligconv-pipeline.dot")

    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=multiprocessing.cpu_count()))
        client = cluster.client()
        submitted_job = client.submit(job)
        client.wait_for_jobs([submitted_job])


@cli.command()
def awh():
    workdir = Path("experiment/awh-hq")
    shutil.rmtree(workdir, ignore_errors=True)

    job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))

    awh_ctx = AWHContext.from_ligconv_edge_dir(
        tools=AWHTools(gmx=Gromacs()),
        edge_dir=LigConvEdgeDir(
            Path("experiment/ligconv-hq/p38/edge_p38a_2aa_p38a_2bb/amber"), edge
        ),
        protein_ff=ProteinForcefield.Amber99SB_ILDN,
        workdir=workdir,
    )

    awh_pipeline(job, [], awh_ctx)
    visualize_job(job, "awh-pipeline.dot")

    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=multiprocessing.cpu_count()))
        client = cluster.client()
        submitted_job = client.submit(job)
        client.wait_for_jobs([submitted_job])


if __name__ == "__main__":
    cli()
