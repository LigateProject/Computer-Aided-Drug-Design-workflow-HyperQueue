import dataclasses
from typing import List, Optional

from hyperqueue import Job
from hyperqueue.task.task import Task


@dataclasses.dataclass
class HqCtx:
    job: Job
    deps: List[Task] = dataclasses.field(default_factory=list)

    def with_dep(self, task: Optional[Task]) -> "HqCtx":
        if task is None:
            return self.with_deps([])
        return self.with_deps([task])

    def with_deps(self, deps: List[Task]) -> "HqCtx":
        return HqCtx(
            job=self.job,
            deps=deps
        )
