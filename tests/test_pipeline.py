import hyperqueue
from hyperqueue import Job

from ligate.awh.ligen.common import LigenTaskContext
from ligate.awh.pipeline.ligen import (
    VirtualScreeningPipelineConfig,
    hq_submit_ligen_virtual_screening_workflow,
)
from ligate.utils.paths import active_workdir
from .utils.io import check_dirs_are_equal


def test_ligen_pipeline(ligen_ctx: LigenTaskContext, tmp_path, data_dir):
    with active_workdir(tmp_path):
        job = Job()
        workdir = tmp_path / "ligen"

        awh_dir = data_dir / "awh" / "1"
        awh_input = awh_dir / "input"

        screening_config = VirtualScreeningPipelineConfig(
            input_smi=awh_input / "ligands.smi",
            input_mol2=awh_input / "crystal.mol2",
            input_protein=awh_input / "protein.pdb",
            max_molecules_per_smi=1,
        )
        hq_submit_ligen_virtual_screening_workflow(
            ligen_ctx,
            workdir,
            config=screening_config,
            job=job,
            deps=[],
        )
        submit_job(job)
        check_dirs_are_equal(
            awh_dir / "01-vscreening-output",
            workdir / "outputs",
        )


def submit_job(job: Job):
    with hyperqueue.cluster.LocalCluster() as cluster:
        cluster.start_worker()
        client = cluster.client()
        submitted = client.submit(job)
        client.wait_for_jobs([submitted])
