import logging
import multiprocessing
import os
import shutil
from pathlib import Path
from typing import Optional

import typer
from hyperqueue import Job, LocalCluster
from hyperqueue.cluster import WorkerConfig
from hyperqueue.task.function import PythonEnv

from ligate.awh.pipeline.virtual_screening.ligen.common import LigenTaskContext
from ligate.awh.pipeline.virtual_screening.ligen.container import ensure_directory
from ligate.awh.pipeline.virtual_screening.ligen.expansion import (
    ExpansionConfig,
    create_expansion_configs_from_smi,
    ligen_expand_smi,
)
from ligate.awh.pipeline.virtual_screening.ligen.virtual_screening import (
    ScreeningConfig,
)
from ligate.awh.pipeline.virtual_screening.tasks import (
    SubmittedExpansion,
    hq_submit_expansion,
    hq_submit_screening,
)

ROOT = Path(__file__).absolute().parent
DATA_DIR = ROOT / "ligenApptainer" / "example"

# CONTAINER_PATH = Path("/mnt/proj1/dd-22-9/dgadioli/integration_ligen5/ligen.sif")
CONTAINER_PATH = Path("/projects/it4i/ligate/cadd/ligen.sif")


app = typer.Typer()


@app.command()
def expand(path: Path, name: Optional[str] = None):
    if name is None:
        name = path.stem
    ligen_expand_smi(
        LigenTaskContext(workdir=Path(os.getcwd()), container_path=CONTAINER_PATH),
        ExpansionConfig(
            id=name, input_smi=path, output_smi=Path(f"{name}.expanded.smi")
        ),
    )


def create_screening_config(task: SubmittedExpansion) -> ScreeningConfig:
    return ScreeningConfig(
        input_mol2=DATA_DIR / "crystal.mol2",
        input_pdb=DATA_DIR / "protein.pdb",
        input_expanded_smi=task.config.output_smi,
        input_protein_name="1CVU",
        output_path=Path(f"screening-{task.config.id}.csv"),
        cores=8,
    )


@app.command()
def workflow(input_smi: Path, max_molecules: int = 100):
    shutil.rmtree("ligen-work", ignore_errors=True)
    workdir = ensure_directory("ligen-work")
    inputs = ensure_directory(workdir / "expansion" / "inputs")
    outputs = ensure_directory(workdir / "expansion" / "outputs")

    ctx = LigenTaskContext(
        workdir=workdir, container_path=Path(CONTAINER_PATH).absolute()
    )

    expansion_configs = create_expansion_configs_from_smi(
        input_smi=input_smi,
        workdir_inputs=inputs,
        workdir_outputs=outputs,
        max_molecules=max_molecules,
    )

    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=multiprocessing.cpu_count()))

        client = cluster.client(
            python_env=PythonEnv(
                prologue=f"""export PYTHONPATH=$PYTHONPATH:{os.getcwd()}"""
            )
        )
        job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))
        expand_tasks = []
        for config in expansion_configs:
            expand_tasks.append(hq_submit_expansion(ctx, config, job))

        [
            hq_submit_screening(ctx, create_screening_config(task), task, job)
            for task in expand_tasks
        ]

        submitted = client.submit(job)

        client.wait_for_jobs([submitted])


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    app()
