from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from . import MinimizationParams
from .add_ions import add_ions
from .minimization import energy_minimize
from .solvate import solvate
from ..hq import HqCtx
from ...common import ComplexOrLigand
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@trace_fn()
def minimize(input: ComplexOrLigand, params: MinimizationParams, gmx: Gromacs):
    solvate(input, gmx)
    add_ions(input, params, gmx)
    energy_minimize(input, params, gmx)


def hq_submit_minimization(
        item: ComplexOrLigand,
        params: MinimizationParams,
        gmx: Gromacs,
        hq: HqCtx,
) -> Task:
    return hq.job.function(
        minimize,
        args=(item, params, gmx),
        name=f"minimize-{item.edge}-{item.pose}-{item.kind}",
        resources=ResourceRequest(cpus=params.cores),
        deps=hq.deps
    )
