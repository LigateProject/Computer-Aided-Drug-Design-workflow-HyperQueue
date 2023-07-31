import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task

from .common import LigenTaskContext
from .container import ligen_container
from ..utils.io import split_file_by_lines


logger = logging.getLogger(__name__)


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
    logger.info(f"Starting expansion of {config.input_smi}")
    with ligen_container(container=ctx.container_path) as ligen:
        smi_input = ligen.map_input(config.input_smi)
        smi_output = ligen.map_output(config.output_smi)
        ligen.run(
            f"ligen-type < {smi_input} | ligen-coordinates | ligen-minimize > {smi_output}",
        )
    logger.info(f"Finished expansion of {config.input_smi}")


def submit_expansion(
    ctx: LigenTaskContext, config: ExpandConfig, job: Job
) -> SubmittedExpansion:
    task = job.function(
        expand_task,
        args=(
            ctx,
            config,
        ),
        name=f"expansion-{config.input_smi.name}",
    )
    return SubmittedExpansion(config=config, task=task)


def create_configs_from_smi(
    input_smi: Path, workdir_inputs: Path, workdir_outputs: Path, max_molecules: int
) -> List[ExpandConfig]:
    """
    Splits a single SMI database into multiple files, so that each file has at most `max_molecules`
    molecules.
    The files will be stored into `workdir`.
    Returns a list of expansion configs for the created files.
    """
    configs = []
    basename = input_smi.stem
    for (index, section) in enumerate(
        split_file_by_lines(input_smi, max_lines=max_molecules)
    ):
        name = f"{basename}-{index}"
        input_path = workdir_inputs / f"{name}.smi"
        with open(input_path, "w") as f:
            f.write(section)
        output_path = workdir_outputs / f"{name}.mol2"
        configs.append(
            ExpandConfig(id=name, input_smi=input_path, output_smi=output_path)
        )
    return configs
