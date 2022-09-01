from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task

from .ctx import AWHContext
from .solvate_minimize import MinimizationParams, solvate_prepare_task


def awh_pipeline(job: Job, deps: List[Task], ctx: AWHContext):
    minimization_params = MinimizationParams(steps=100)
    solvate_prepare_task(job, deps, ctx, minimization_params)

    # equilibrate_params = EquilibrateParams(steps=100)
    # equilibrate_output = equilibrate(ctx, triple, equilibrate_params, minimization_output, job)

    # awh_params = AWHParams(steps=5000, diffusion=0.005, replicates=3)
    # awh_output = awh(ctx, triple, awh_params, equilibrate_output, job)
    #
    # analyze(ctx, awh_output, job)
