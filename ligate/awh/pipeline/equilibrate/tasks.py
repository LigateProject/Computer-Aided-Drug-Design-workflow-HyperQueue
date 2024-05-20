from hyperqueue import Job
from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from . import EquilibrateParams, equilibrate
from ....wrapper.gromacs import Gromacs


def hq_submit_equilibrate(
        params: EquilibrateParams,
        gmx: Gromacs,
        job: Job,
) -> Task:
    return job.function(
        equilibrate,
        args=(
            params,
            gmx,
        ),
        name=f"equilibrate-{params.file.stem}",
        resources=ResourceRequest(cpus=params.cores),
    )
