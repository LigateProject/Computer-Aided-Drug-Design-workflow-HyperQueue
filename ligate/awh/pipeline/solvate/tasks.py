import dataclasses
from typing import List

from hyperqueue.task.task import Task

from . import solvate
from ..common import EdgeSet
from ..hq import HqCtx
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class SolvatedPose:
    ligand: str
    pose: str
    ligand_task: Task
    complex_task: Task


@dataclasses.dataclass
class SubmittedSolvate:
    edge_set: EdgeSet
    poses: List[SolvatedPose]

    def tasks(self) -> List[Task]:
        def gen():
            for pose in self.poses:
                yield pose.ligand_task
                yield pose.complex_task
        return list(gen())


def hq_submit_solvate(
        edge_set: EdgeSet,
        gmx: Gromacs,
        hq: HqCtx,
) -> SubmittedSolvate:
    poses = []

    for ligand in edge_set.ligands:
        for pose in ligand.poses:
            pose_dir = ligand.pose_dir(pose)
            ligand_task = hq.job.function(
                lambda: solvate(pose_dir=pose_dir, gmx=gmx, kind="ligand"),
                name=f"solvate-{ligand.name()}-{pose}-ligand",
                deps=hq.deps
            )
            complex_task = hq.job.function(
                lambda: solvate(pose_dir=pose_dir, gmx=gmx, kind="complex"),
                name=f"solvate-{ligand.name()}-{pose}-complex",
                deps=hq.deps
            )
            poses.append(SolvatedPose(
                ligand=ligand.name(),
                pose=pose,
                ligand_task=ligand_task,
                complex_task=complex_task
            ))
    return SubmittedSolvate(
        edge_set=edge_set,
        poses=poses
    )
