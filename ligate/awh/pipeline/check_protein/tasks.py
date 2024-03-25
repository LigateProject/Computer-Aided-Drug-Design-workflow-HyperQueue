from pathlib import Path

from hyperqueue import Job
from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from . import check_protein


def hq_submit_check_protein(
    pdb: Path,
    workdir: Path,
    job: Job,
) -> Task:
    return job.function(
        check_protein,
        args=(
            pdb,
            workdir,
        ),
        name=f"check-protein-{pdb.name}",
        resources=ResourceRequest(cpus=8),
    )
