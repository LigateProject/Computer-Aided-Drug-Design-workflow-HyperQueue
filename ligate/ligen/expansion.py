from dataclasses import dataclass
from pathlib import Path

from hyperqueue import Job
from hyperqueue.task.task import Task

from .common import LigenTaskContext
from .container import ligen_container


@dataclass
class ExpandConfig:
    id: str
    input_smi: Path
    output_smi: Path


@dataclass
class SubmittedExpansion:
    config: ExpandConfig
    task: Task


def expand_task(ctx: LigenTaskContext, config: ExpandConfig):
    with ligen_container(container=ctx.container_path) as ligen:
        smi_input = ligen.map_input(config.input_smi)
        smi_output = ligen.map_output(config.output_smi)
        ligen.run(
            f"ligen-type < {smi_input} | ligen-coordinates | ligen-minimize > {smi_output}",
        )


def submit_expansion(ctx: LigenTaskContext, config: ExpandConfig, job: Job) -> SubmittedExpansion:
    task = job.function(
        expand_task,
        args=(
            ctx,
            config,
        ),
        name=f"expansion-{config.input_smi.name}",
    )
    return SubmittedExpansion(config=config, task=task)
