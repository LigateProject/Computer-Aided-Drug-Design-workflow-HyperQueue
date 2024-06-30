from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from . import EquilibrateParams, equilibrate
from ..hq import HqCtx
from ...common import ComplexOrLigand
from ....wrapper.gromacs import Gromacs


def hq_submit_equilibrate(
        item: ComplexOrLigand,
        params: EquilibrateParams,
        gmx: Gromacs,
        hq: HqCtx,
) -> Task:
    return hq.job.function(
        equilibrate,
        args=(
            item,
            params,
            gmx,
        ),
        name=f"equilibrate-{item.edge}-{item.pose}-{item.kind}",
        resources=ResourceRequest(cpus=params.cores),
        deps=hq.deps
    )
