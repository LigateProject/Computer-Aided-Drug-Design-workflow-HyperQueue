from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from . import CreateHybridLigandsParams, create_hybrid_ligands
from ..hq import HqCtx
from ....wrapper.gromacs import Gromacs


def hq_submit_hybrid_ligands(
    params: CreateHybridLigandsParams,
    gmx: Gromacs,
    hq: HqCtx,
) -> Task:
    return hq.job.function(
        create_hybrid_ligands,
        args=(
            params,
            gmx,
        ),
        name="create-hybrid-ligands",
        resources=ResourceRequest(cpus=params.cores),
        deps=hq.deps
    )
