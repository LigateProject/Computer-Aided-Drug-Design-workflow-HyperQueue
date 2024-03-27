import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import List

from hyperqueue import Job
from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from .expansion import SubmittedExpansion, hq_submit_expansion
from ..ligen.common import LigenTaskContext
from ..ligen.expansion import (
    create_expansion_configs_from_smi,
)
from ..ligen.virtual_screening import ScreeningConfig, ligen_screen_ligands
from ...utils.io import ensure_directory


@dataclass
class SubmittedScreening:
    config: ScreeningConfig
    task: Task


def hq_submit_screening(
    ctx: LigenTaskContext,
    config: ScreeningConfig,
    expansion_submit: SubmittedExpansion,
    job: Job,
) -> SubmittedScreening:
    task = job.function(
        ligen_screen_ligands,
        args=(
            ctx,
            config,
        ),
        deps=(expansion_submit.task,),
        name=f"screening-{config.output_scores_csv.name}",
        resources=ResourceRequest(cpus=config.cores),
    )
    return SubmittedScreening(config=config, task=task)


@dataclasses.dataclass
class VirtualScreeningPipelineConfig:
    input_smi: Path
    input_mol2: Path
    input_protein: Path

    max_molecules_per_smi: int = 10


@dataclasses.dataclass
class SubmittedVirtualScreeningPipeline:
    tasks: List[Task]
    output_scores_csv: Path


def merge_csvs(csv_paths: List[Path], output: Path):
    import pandas as pd

    df = pd.concat((pd.read_csv(csv) for csv in csv_paths))
    df.to_csv(output, index=False)


def hq_submit_ligen_virtual_screening_workflow(
    ctx: LigenTaskContext,
    workdir: Path,
    config: VirtualScreeningPipelineConfig,
    job: Job,
    deps: List[Task],
) -> SubmittedVirtualScreeningPipeline:
    workdir_inputs = ensure_directory(workdir / "inputs")
    workdir_outputs = ensure_directory(workdir / "outputs")
    output_csv = workdir_outputs / "scores.csv"

    def create_screening_config(task: SubmittedExpansion) -> ScreeningConfig:
        return ScreeningConfig(
            input_probe_mol2=config.input_mol2,
            input_protein_pdb=config.input_protein,
            input_expanded_mol2=task.config.output_mol2,
            input_protein_name="1CVU",
            output_scores_csv=workdir_outputs / f"screening-{task.config.id}.csv",
            cores=8,
        )

    expansion_configs = create_expansion_configs_from_smi(
        input_smi=config.input_smi,
        workdir_inputs=workdir_inputs,
        workdir_outputs=workdir_outputs,
        max_molecules=config.max_molecules_per_smi,
    )

    expand_tasks = []
    for c in expansion_configs:
        expand_tasks.append(hq_submit_expansion(ctx, c, deps, job))

    screening_configs = [create_screening_config(task) for task in expand_tasks]
    screen_tasks = [
        hq_submit_screening(ctx, c, task, job).task
        for (c, task) in zip(screening_configs, expand_tasks)
    ]
    csv_paths = [config.output_scores_csv for config in screening_configs]
    merge_csv_task = job.function(
        merge_csvs, args=(csv_paths, output_csv), deps=screen_tasks
    )

    return SubmittedVirtualScreeningPipeline(
        output_scores_csv=output_csv, tasks=[merge_csv_task]
    )
