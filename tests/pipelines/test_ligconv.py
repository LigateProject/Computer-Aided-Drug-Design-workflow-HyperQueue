import pytest
from hyperqueue import Job, LocalCluster
from hyperqueue.cluster import WorkerConfig
from hyperqueue.visualization import visualize_job

from ligate.ligconv.common import LigandForcefield, ProteinForcefield
from ligate.pipelines.ligconv import LigConvContext, ligconv_pipeline
from ligate.pipelines.ligconv.common import (
    Edge,
    LigConvParameters,
    LigConvTools,
    LigenOutputData,
)
from ligate.wrapper.babel import Babel
from ligate.wrapper.gromacs import Gromacs
from ligate.wrapper.stage import Stage


@pytest.mark.slow
def test_ligconv_pipeline(gmx: Gromacs, babel: Babel, stage: Stage, tmp_path, data_dir):
    workdir = tmp_path / "experiment"

    ligen_output = LigenOutputData(
        protein_file=data_dir / "ligen/p38/protein_amber/protein.pdb",
        ligand_dir=data_dir / "ligen/p38/ligands_gaff2",
    )
    ligconv_params = LigConvParameters(
        protein_ff=ProteinForcefield.Amber99SB_ILDN,
        ligand_ff=LigandForcefield.Gaff2,
        edges=[Edge("p38a_2aa", "p38a_2bb")],
    )

    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=2))
        client = cluster.client()

        ligconv_ctx = LigConvContext(
            workdir=workdir,
            params=ligconv_params,
            ligen_data=ligen_output,
            tools=LigConvTools(gmx=gmx, babel=babel, stage=stage),
        )

        job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))

        ligconv_pipeline(job, ligconv_ctx)

        visualize_job(job, tmp_path / "ligconv.dot")
        submitted_job = client.submit(job)
        client.wait_for_jobs([submitted_job])
