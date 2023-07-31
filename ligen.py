import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional

import typer
from hyperqueue import Job, LocalCluster
from hyperqueue.cluster import WorkerConfig
from hyperqueue.task.function import PythonEnv

from ligate.ligen.common import LigenTaskContext
from ligate.ligen.container import ensure_directory
from ligate.ligen.expansion import ExpandConfig, SubmittedExpansion, expand_task, submit_expansion
from ligate.ligen.virtual_screening import ScreeningConfig, submit_screening

ROOT = Path(__file__).absolute().parent
DATA_DIR = ROOT / "ligenApptainer" / "example"

# CONTAINER_PATH = Path("/mnt/proj1/dd-22-9/dgadioli/integration_ligen5/ligen.sif")
CONTAINER_PATH = Path("/projects/it4i/ligate/cadd/ligen.sif")


app = typer.Typer()


@app.command()
def expand(path: Path, name: Optional[str] = None):
    if name is None:
        name = path.stem
    expand_task(
        LigenTaskContext(workdir=Path(os.getcwd()), container_path=CONTAINER_PATH),
        ExpandConfig(id=name, input_smi=path, output_smi=Path(f"{name}.expanded.smi"))
    )


def gather_expand_configs() -> List[ExpandConfig]:
    configs = []
    for i in range(1):
        config = ExpandConfig(
            id=str(i),
            input_smi=DATA_DIR / "ligands.smi",
            output_smi=Path(f"expansion-{i}.smi")
        )
        configs.append(config)
    return configs


def create_screening_config(task: SubmittedExpansion) -> ScreeningConfig:
    return ScreeningConfig(
        input_mol2=DATA_DIR / "crystal.mol2",
        input_pdb=DATA_DIR / "protein.pdb",
        output_path=Path(f"screening-{task.config.id}.csv"),
        input_protein_name="1CVU",
        ligand_expansion=task,
        cores=8
    )


@app.command()
def workflow():
    shutil.rmtree("ligen-work", ignore_errors=True)
    workdir = ensure_directory("ligen-work")

    ctx = LigenTaskContext(workdir=workdir, container_path=Path(CONTAINER_PATH).absolute())

    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=1))

        client = cluster.client(
            python_env=PythonEnv(
                prologue=f"""export PYTHONPATH=$PYTHONPATH:{os.getcwd()}"""
            )
        )
        job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))
        expand_configs = gather_expand_configs()
        expand_tasks = []
        for config in expand_configs:
            expand_tasks.append(submit_expansion(ctx, config, job))

        [submit_screening(ctx, create_screening_config(task), job) for task in expand_tasks]

        submitted = client.submit(job)

        client.wait_for_jobs([submitted])


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    app()
