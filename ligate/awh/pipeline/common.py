import dataclasses
from pathlib import Path
from typing import List

from ...utils.io import iterate_directories


@dataclasses.dataclass
class Edge:
    directory: Path
    poses: List[str]

    def name(self) -> str:
        return self.directory.name

    def pose_dir(self, name: str) -> Path:
        return self.directory / name


@dataclasses.dataclass
class EdgeSet:
    directory: Path
    ligands: List[Edge]


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
