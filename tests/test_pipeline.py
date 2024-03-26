import hyperqueue
from hyperqueue import Job

from ligate.awh.ligen.common import LigenTaskContext
from ligate.awh.pipeline.ligen import hq_submit_ligen_workflow
from ligate.utils.paths import active_workdir
from .utils.io import check_files_are_equal


def test_ligen_pipeline(ligen_ctx: LigenTaskContext, tmp_path, data_dir):
    with active_workdir(tmp_path):
        job = Job()
        workdir = tmp_path / "ligen"

        awh_dir = data_dir / "awh" / "1"
        awh_input = awh_dir / "input"
        hq_submit_ligen_workflow(
            ligen_ctx,
            workdir,
            input_smi=awh_input / "ligands.smi",
            input_mol2=awh_input / "crystal.mol2",
            input_protein=awh_input / "protein.pdb",
            job=job,
            deps=[],
        )
        submit_job(job)
        check_files_are_equal(
            awh_dir / "ligen-output" / "ligands.mol2",
            workdir / "outputs" / "ligands-0.mol2",
        )
        check_files_are_equal(
            awh_dir / "ligen-output" / "screening.csv",
            workdir / "outputs" / "screening-ligands-0.csv",
        )


def submit_job(job: Job):
    with hyperqueue.cluster.LocalCluster() as cluster:
        cluster.start_worker()
        client = cluster.client()
        submitted = client.submit(job)
        client.wait_for_jobs([submitted])
