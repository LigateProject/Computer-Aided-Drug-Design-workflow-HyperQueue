import multiprocessing
from pathlib import Path

from hyperqueue import Job, LocalCluster
from hyperqueue.cluster import WorkerConfig
from hyperqueue.visualization import visualize_job

from ligate.ligconv.common import LigandForcefield, ProteinForcefield
from ligate.pipelines.ligconv import ligconv_pipeline
from ligate.pipelines.ligconv.common import Edge, LigConvContext, LigConvParameters, LigConvTools, \
    LigenOutputData
from ligate.wrapper.babel import Babel
from ligate.wrapper.gmx import GMX
from ligate.wrapper.stage import Stage

gmx = GMX()
babel = Babel()
stage = Stage()

workdir = Path("experiment/workdir-hq")
# shutil.rmtree(workdir, ignore_errors=True)

ligen_output = LigenOutputData(
    protein_file=Path("ligen/output/p38/protein_amber/protein.pdb"),
    ligand_dir=Path("ligen/output/p38/ligands_gaff2")
)
ligconv_params = LigConvParameters(
    protein_ff=ProteinForcefield.Amber99SB_ILDN,
    ligand_ff=LigandForcefield.Gaff2,
    edges=[Edge("p38a_2aa", "p38a_2bb")]
)

with LocalCluster() as cluster:
    cluster.start_worker(WorkerConfig(cores=multiprocessing.cpu_count()))
    client = cluster.client()

    ligconv_ctx = LigConvContext(
        workdir=workdir,
        params=ligconv_params,
        ligen_data=ligen_output,
        tools=LigConvTools(
            gmx=gmx,
            babel=babel,
            stage=stage
        )
    )

    job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))

    # Convert outputs from LiGen to GROMACS-compatible inputs
    edge_task_state = ligconv_pipeline(job, ligconv_ctx)

    visualize_job(job, "job-ligconv.dot")
    submitted_job = client.submit(job)
    client.wait_for_jobs([submitted_job])

    # Run AWH pipeline
    # job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))

    # TODO: wait for tasks
    # awh_pipeline(job, ligconv_ctx, ligconv_params.edges[0], gmx=gmx)
    # submitted_job = client.submit(job)
    # client.wait_for_jobs([submitted_job])
