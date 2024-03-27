from dataclasses import dataclass

from hyperqueue import Job
from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from ..ligen.common import LigenTaskContext
from ..ligen.docking import DockingConfig, ligen_dock
from .expansion import SubmittedExpansion


@dataclass
class SubmittedDocking:
    config: DockingConfig
    task: Task


def hq_submit_docking(
    ctx: LigenTaskContext,
    config: DockingConfig,
    expansion_submit: SubmittedExpansion,
    job: Job,
) -> SubmittedDocking:
    task = job.function(
        ligen_dock,
        args=(
            ctx,
            config,
        ),
        deps=(expansion_submit.task,),
        name=f"docking-{config.output_poses_mol2.name}",
        resources=ResourceRequest(cpus=config.cores),
    )
    return SubmittedDocking(config=config, task=task)
