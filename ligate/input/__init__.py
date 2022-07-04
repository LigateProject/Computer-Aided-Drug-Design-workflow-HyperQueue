import dataclasses
import enum
from pathlib import Path
from typing import List


class Protein(enum.Enum):
    Bace = enum.auto()

    def __repr__(self) -> str:
        return self.name


class ForceField(enum.Enum):
    Amber = enum.auto()

    def __repr__(self) -> str:
        return self.name


Mutation = str


@dataclasses.dataclass
class ComputationTriple:
    protein: Protein
    mutation: Mutation
    forcefield: ForceField

    def __repr__(self) -> str:
        return f"(protein {self.protein}, mutation {self.mutation}, forcefield {self.forcefield})"


@dataclasses.dataclass
class GeneratedInput:
    pdb_files: List[Path]


class InputProvider:
    def provide_input(self, input: ComputationTriple, directory: Path):
        raise NotImplementedError
