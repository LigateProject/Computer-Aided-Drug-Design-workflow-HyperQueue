import dataclasses
from pathlib import Path
from typing import Generator, List, Optional, Tuple

from hyperqueue.task.task import Task

from ..common import ComplexOrLigand
from ...utils.io import iterate_directories


Pose = str


@dataclasses.dataclass
class Edge:
    directory: Path
    poses: List[Pose]

    def name(self) -> str:
        return self.directory.name

    def pose_dir(self, name: Pose) -> Path:
        return self.directory / name


@dataclasses.dataclass
class EdgeSet:
    directory: Path
    edges: List[Edge]

    def iterate_poses(self) -> Generator[Tuple[Edge, Pose], None, None]:
        for edge in self.edges:
            for pose in edge.poses:
                yield (edge, pose)


@dataclasses.dataclass
class ComplexOrLigandTask:
    edge: Edge
    pose: Pose
    item: ComplexOrLigand
    task: Optional[Task] = None


def construct_edge_set_from_dir(directory: Path) -> EdgeSet:
    ligands = []
    for path in iterate_directories(directory):
        if path.name.startswith("edge"):
            poses = []
            for pose_path in iterate_directories(path):
                if pose_path.name.startswith("pose"):
                    poses.append(pose_path.name)
            ligands.append(Edge(directory=path, poses=poses))
    return EdgeSet(directory, ligands)
