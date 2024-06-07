from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from . import PrepareProductionSimulationParams, prepare_production_simulation
from ..hq import HqCtx
from ....wrapper.gromacs import Gromacs


def hq_submit_prepare_production_simulation(
    params: PrepareProductionSimulationParams,
    gmx: Gromacs,
    hq: HqCtx,
) -> Task:
    return hq.job.function(
        prepare_production_simulation,
        args=(
            params,
            gmx,
        ),
        name="prepare-production-simulation",
        resources=ResourceRequest(cpus=params.cores),
        deps=hq.deps
    )
