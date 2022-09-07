from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task

from .awh import AWHParams, awh_task
from .ctx import AWHContext
from .equilibrate import EquilibrateParams, equilibrate_task
from .solvate_minimize import MinimizationParams, solvate_prepare_task


def awh_pipeline(job: Job, deps: List[Task], ctx: AWHContext):
    minimization_params = MinimizationParams(steps=100)
    minimization_output = solvate_prepare_task(job, deps, ctx, minimization_params)

    equilibrate_params = EquilibrateParams(steps=100)
    equilibrate_output = equilibrate_task(
        job, ctx, equilibrate_params, minimization_output
    )

    awh_params = AWHParams(steps=5000, diffusion=0.005, replicates=3)
    awh_output = awh_task(job, ctx, awh_params, equilibrate_output)

    # analyze(ctx, awh_output, job)
