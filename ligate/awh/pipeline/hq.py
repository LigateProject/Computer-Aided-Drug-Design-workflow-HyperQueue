import dataclasses
from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task


@dataclasses.dataclass
class HqCtx:
    job: Job
    deps: List[Task] = dataclasses.field(default_factory=list)

    def with_dep(self, task: Task) -> "HqCtx":
        return self.with_deps([task])

    def with_deps(self, deps: List[Task]) -> "HqCtx":
        return HqCtx(
            job=self.job,
            deps=deps
        )
