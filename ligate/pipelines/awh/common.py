import dataclasses
import enum
from pathlib import Path

from ...input import ComputationTriple
from ...input.properties import protein_ff
from ...wrapper.gmx import GMX

DATA_DIR = Path(__file__).absolute().parent / "data"

EM_L0_MDP = DATA_DIR / "em_l0.mdp"
EQ_NVT_L0_MDP = DATA_DIR / "eq_nvt_l0.mdp"
PRODUCTION_MDP = DATA_DIR / "production.mdp"


class LigandOrProtein(enum.Enum):
    Ligand = enum.auto()
    Protein = enum.auto()

    def __repr__(self) -> str:
        return self.name


@dataclasses.dataclass
class LopWorkload:
    lop: LigandOrProtein
    directory: Path

    def __repr__(self) -> str:
        return f"{self.lop} at `{str(self.directory)}`"


TopName = str


def topology_path(topname: TopName) -> str:
    return f"topology/topol_{topname}.top"


def get_topname(lop: LigandOrProtein, triple: ComputationTriple) -> TopName:
    return {
        LigandOrProtein.Ligand: "ligandInWater",
        LigandOrProtein.Protein: protein_ff(triple),
    }[lop]


@dataclasses.dataclass
class AWHTools:
    gmx: GMX
