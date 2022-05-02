import enum

from ..input import ComputationTriple
from ..input.properties import protein_ff


class LigandOrProtein(enum.Enum):
    Ligand = enum.auto()
    Protein = enum.auto()

    def __repr__(self) -> str:
        return self.name


TopName = str


def topology_path(topname: TopName) -> str:
    return f"topology/topol_{topname}.top"


def get_topname(lop: LigandOrProtein, triple: ComputationTriple) -> TopName:
    return {
        LigandOrProtein.Ligand: "ligandInWater",
        LigandOrProtein.Protein: protein_ff(triple)
    }[lop]
