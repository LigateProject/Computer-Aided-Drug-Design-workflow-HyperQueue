import logging
from pathlib import Path

import hyperqueue.cluster
from hyperqueue import Job
from hyperqueue.visualization import visualize_job

from ligate.awh.ligen.common import LigenTaskContext
from ligate.awh.pipeline.check_protein.tasks import hq_submit_check_protein
from ligate.awh.pipeline.docking import (
    DockingPipelineConfig,
    hq_submit_ligen_docking_workflow,
)
from ligate.awh.pipeline.select_ligands import (
    LigandSelectionConfig,
    hq_submit_select_ligands,
)
from ligate.awh.pipeline.virtual_screening import (
    VirtualScreeningPipelineConfig,
    hq_submit_ligen_virtual_screening_workflow,
)
from ligate.utils.io import ensure_directory

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    DATA_DIR = Path("data/awh-3").absolute()
    WORKDIR = Path("workdir").absolute()

    WORKDIR = ensure_directory(WORKDIR, clear=True)

    protein_pdb = DATA_DIR / "protein.pdb"

    ligen_container_path = Path("ligen.sif").absolute()
    vscreening_workdir = WORKDIR / "ligen-vscreening"
    ligen_ctx = LigenTaskContext(
        workdir=vscreening_workdir, container_path=ligen_container_path
    )

    job = Job(default_workdir=WORKDIR / "hq", default_env=dict(HQ_PYLOG="DEBUG"))
    task = hq_submit_check_protein(protein_pdb, WORKDIR, job)

    # Perform virtual screening. Expand SMI into MOL2, and generate a CSV with scores for each
    # ligand in the input SMI file.
    probe_mol2 = DATA_DIR / "probe.mol2"
    screening_config = VirtualScreeningPipelineConfig(
        input_smi=DATA_DIR / "ligands.smi",
        input_probe_mol2=probe_mol2,
        input_protein=protein_pdb,
        max_molecules_per_smi=1,
    )
    output = hq_submit_ligen_virtual_screening_workflow(
        ligen_ctx,
        vscreening_workdir,
        config=screening_config,
        job=job,
        deps=[task],
    )

    # Select best N ligands based on the assigned scores, and generate a new SMI file with the
    # best ligands.
    best_ligands_smi = WORKDIR / "selected-ligands.smi"
    selection_config = LigandSelectionConfig(
        input_smi=screening_config.input_smi,
        scores_csv=output.output_scores_csv,
        output_smi=best_ligands_smi,
        n_ligands=42,
    )
    select_task = hq_submit_select_ligands(selection_config, job, output.tasks)

    # Dock the best ligands.
    docking_config = DockingPipelineConfig(
        input_smi=best_ligands_smi,
        input_probe_mol2=probe_mol2,
        input_protein=protein_pdb,
    )
    output = hq_submit_ligen_docking_workflow(
        ligen_ctx, WORKDIR / "ligen-docking", docking_config, job, deps=[select_task]
    )

    visualize_job(job, "job.dot")

    # Run the workflow
    with hyperqueue.cluster.LocalCluster() as cluster:
        cluster.start_worker()
        client = cluster.client()
        submitted = client.submit(job)
        client.wait_for_jobs([submitted])
    print(f"Docked MOL2 can be found at {output.docked_mol2}")
