import dataclasses
from typing import Dict, Generic, List, TypeVar

from hyperqueue.task.task import Task

from .ligconv.common import Edge


@dataclasses.dataclass
class LigandTaskMapping:
    ligand_to_task: Dict[str, Task]

    def get_ligand_task(self, ligand_name: str) -> Task:
        return self.ligand_to_task[ligand_name]


@dataclasses.dataclass
class EdgeTaskMapping:
    edge_to_task: Dict[Edge, Task]

    def get_edge_task(self, edge: Edge) -> Task:
        return self.edge_to_task[edge]


Key = TypeVar("Key")


@dataclasses.dataclass
class TaskMapping(Generic[Key]):
    map: Dict[Key, Task]

    def get_task(self, key: Key) -> Task:
        return self.map[key]

    def all_tasks(self) -> List[Task]:
        return list(self.map.values())
