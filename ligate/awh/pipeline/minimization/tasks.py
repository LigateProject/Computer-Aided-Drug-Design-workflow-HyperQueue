import dataclasses
from typing import List

from hyperqueue.task.task import Task

from . import MinimizationParams
from .add_ions import add_ions
from .solvate import solvate
from ..common import EdgeSet
from ..hq import HqCtx
from ...paths import Complex, ComplexOrLigand, Ligand
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class SolvatedPose:
    ligand: str
    pose: str
    ligand_task: Task
    complex_task: Task


@dataclasses.dataclass
class SubmittedMinimization:
    edge_set: EdgeSet
    poses: List[SolvatedPose]

    def tasks(self) -> List[Task]:
        def gen():
            for pose in self.poses:
                yield pose.ligand_task
                yield pose.complex_task
        return list(gen())


@trace_fn()
def minimize(input: ComplexOrLigand, params: MinimizationParams, gmx: Gromacs):
    solvate(input, gmx)
    add_ions(input, params, gmx)


def hq_submit_minimization(
        edge_set: EdgeSet,
        params: MinimizationParams,
        gmx: Gromacs,
        hq: HqCtx,
) -> SubmittedMinimization:
    poses = []

    for ligand in edge_set.ligands:
        for pose in ligand.poses:
            pose_dir = ligand.pose_dir(pose)
            ligand_task = hq.job.function(
                minimize,
                args=(Ligand(pose_dir), params, gmx),
                name=f"minimize-{ligand.name()}-{pose}-ligand",
                deps=hq.deps
            )
            complex_task = hq.job.function(
                minimize,
                args=(Complex(pose_dir), params, gmx),
                name=f"minimize-{ligand.name()}-{pose}-complex",
                deps=hq.deps
            )
            poses.append(SolvatedPose(
                ligand=ligand.name(),
                pose=pose,
                ligand_task=ligand_task,
                complex_task=complex_task
            ))
    return SubmittedMinimization(
        edge_set=edge_set,
        poses=poses
    )
