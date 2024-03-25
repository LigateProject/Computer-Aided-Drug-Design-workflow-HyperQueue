from dataclasses import dataclass
from typing import List

from hyperqueue import Job
from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from ...ligen.common import LigenTaskContext
from ...ligen.expansion import ExpansionConfig, ligen_expand_smi
from ...ligen.virtual_screening import ScreeningConfig, ligen_screen_ligands


@dataclass
class SubmittedExpansion:
    config: ExpansionConfig
    task: Task


def hq_submit_expansion(
    ctx: LigenTaskContext, config: ExpansionConfig, deps: List[Task], job: Job
) -> SubmittedExpansion:
    task = job.function(
        ligen_expand_smi,
        args=(
            ctx,
            config,
        ),
        name=f"expansion-{config.input_smi.name}",
        deps=deps,
    )
    return SubmittedExpansion(config=config, task=task)


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
