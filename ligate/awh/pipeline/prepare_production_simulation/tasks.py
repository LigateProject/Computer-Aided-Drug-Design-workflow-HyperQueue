from hyperqueue.task.task import Task

from . import PrepareProductionSimulationParams, prepare_production_simulation
from ..hq import HqCtx
from ...common import ComplexOrLigand
from ....wrapper.gromacs import Gromacs


def hq_submit_prepare_production_simulation(
        item: ComplexOrLigand,
        params: PrepareProductionSimulationParams,
        gmx: Gromacs,
        hq: HqCtx,
) -> Task:
    return hq.job.function(
        prepare_production_simulation,
        args=(
            item,
            params,
            gmx,
        ),
        name=f"prepare-production-simulation-{item.edge}-{item.pose}-{item.kind}",
        deps=hq.deps
    )
