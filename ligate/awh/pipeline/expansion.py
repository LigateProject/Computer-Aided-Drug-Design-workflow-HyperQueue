from dataclasses import dataclass
from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task

from ..ligen.common import LigenTaskContext
from ..ligen.expansion import ExpansionConfig, ligen_expand_smi


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
