import dataclasses
import enum
from pathlib import Path
from typing import List


class Protein(enum.Enum):
    Bace = enum.auto()


class ForceField(enum.Enum):
    Amber = enum.auto()


Mutation = str


@dataclasses.dataclass
class ComputationTriple:
    protein: Protein
    mutation: Mutation
    forcefield: ForceField


@dataclasses.dataclass
class GeneratedInput:
    pdb_files: List[Path]


class InputProvider:
    def provide_input(self, input: ComputationTriple, directory: Path) -> GeneratedInput:
        raise NotImplementedError
