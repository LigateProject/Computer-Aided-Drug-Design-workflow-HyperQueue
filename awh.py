import logging
from pathlib import Path
from typing import List

import hyperqueue.cluster
from hyperqueue import Job
from hyperqueue.task.task import Task

from ligate.awh.input import AWHInput
from ligate.awh.pipeline.check_protein.tasks import hq_submit_check_protein
from ligate.awh.ligen.common import LigenTaskContext
from ligate.awh.ligen.expansion import (
    create_expansion_configs_from_smi,
)
from ligate.awh.ligen.virtual_screening import (
    ScreeningConfig,
)
from ligate.awh.pipeline.virtual_screening.tasks import (
    SubmittedExpansion,
    hq_submit_expansion,
    hq_submit_screening,
)
from ligate.utils.io import ensure_directory


def hq_submit_ligen_workflow(
    ctx: LigenTaskContext,
    workdir: Path,
    input_smi: Path,
    input_mol2: Path,
    input_protein: Path,
    job: Job,
    deps: List[Task],
):
    def create_screening_config(task: SubmittedExpansion) -> ScreeningConfig:
        return ScreeningConfig(
            input_crystal_structure_mol2=input_mol2,
            input_protein_pdb=input_protein,
            input_expanded_mol2=task.config.output_mol2,
            input_protein_name="1CVU",
            output_scores_csv=Path(f"screening-{task.config.id}.csv"),
            cores=8,
        )

    workdir_inputs = ensure_directory(workdir / "inputs")
    workdir_outputs = ensure_directory(workdir / "outputs")

    expansion_configs = create_expansion_configs_from_smi(
        input_smi=input_smi,
        workdir_inputs=workdir_inputs,
        workdir_outputs=workdir_outputs,
        max_molecules=10,
    )

    expand_tasks = []
    for config in expansion_configs:
        expand_tasks.append(hq_submit_expansion(ctx, config, deps, job))

    [
        hq_submit_screening(ctx, create_screening_config(task), task, job)
        for task in expand_tasks
    ]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    DATA_DIR = Path("data/awh").absolute()
    WORKDIR = Path("workdir").absolute()

    WORKDIR = ensure_directory(WORKDIR, clear=True)

    awh_input = AWHInput(protein_pdb=DATA_DIR / "protein_bace_p2_amber.pdb")

    ligen_container_path = Path("ligen.sif").absolute()
    ligen_workdir = WORKDIR / "ligen"
    ligen_ctx = LigenTaskContext(
        workdir=ligen_workdir, container_path=ligen_container_path
    )

    job = Job(default_workdir=WORKDIR / "hq", default_env=dict(HQ_PYLOG="DEBUG"))
    task = hq_submit_check_protein(awh_input.protein_pdb, WORKDIR, job)

    hq_submit_ligen_workflow(
        ligen_ctx,
        ligen_workdir,
        input_smi=DATA_DIR / "input-ab.smi",
        input_mol2=DATA_DIR / "crystal.mol2",
        input_protein=Path("backup/ligenApptainer/example/protein.pdb").absolute(),
        job=job,
        deps=[task],
    )

    # Run the workflow
    with hyperqueue.cluster.LocalCluster() as cluster:
        cluster.start_worker()
        client = cluster.client()
        submitted = client.submit(job)
        client.wait_for_jobs([submitted])
