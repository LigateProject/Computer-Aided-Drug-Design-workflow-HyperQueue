from hyperqueue import Job

from ...wrapper.gmx import GMX
from ..ligconv import LigConvContext
from ..ligconv.common import Edge


def awh_pipeline(job: Job, ctx: LigConvContext, edge: Edge, gmx: GMX):
    pass
    # minimization_params = MinimizationParams(steps=100)
    # minimization_output = solvate_prepare(ctx, edge, minimization_params, job, gmx)

    # equilibrate_params = EquilibrateParams(steps=100)
    # equilibrate_output = equilibrate(ctx, triple, equilibrate_params, minimization_output, job)

    # awh_params = AWHParams(steps=5000, diffusion=0.005, replicates=3)
    # awh_output = awh(ctx, triple, awh_params, equilibrate_output, job)
    #
    # analyze(ctx, awh_output, job)
