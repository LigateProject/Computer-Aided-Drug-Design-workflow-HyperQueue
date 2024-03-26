from pathlib import Path
from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task

from ..ligen.common import LigenTaskContext
from ..ligen.expansion import create_expansion_configs_from_smi
from ..ligen.virtual_screening import ScreeningConfig
from .virtual_screening.tasks import (
    SubmittedExpansion,
    hq_submit_expansion,
    hq_submit_screening,
)
from ...utils.io import ensure_directory


def hq_submit_ligen_workflow(
    ctx: LigenTaskContext,
    workdir: Path,
    input_smi: Path,
    input_mol2: Path,
    input_protein: Path,
    job: Job,
    deps: List[Task],
):
    workdir_inputs = ensure_directory(workdir / "inputs")
    workdir_outputs = ensure_directory(workdir / "outputs")

    def create_screening_config(task: SubmittedExpansion) -> ScreeningConfig:
        return ScreeningConfig(
            input_probe_mol2=input_mol2,
            input_protein_pdb=input_protein,
            input_expanded_mol2=task.config.output_mol2,
            input_protein_name="1CVU",
            output_scores_csv=workdir_outputs / f"screening-{task.config.id}.csv",
            cores=8,
        )

    expansion_configs = create_expansion_configs_from_smi(
        input_smi=input_smi,
        workdir_inputs=workdir_inputs,
        workdir_outputs=workdir_outputs,
        max_molecules=10,
    )

    expand_tasks = []
    for config in expansion_configs:
        expand_tasks.append(hq_submit_expansion(ctx, config, deps, job))

    [hq_submit_screening(ctx, create_screening_config(task), task, job) for task in expand_tasks]
