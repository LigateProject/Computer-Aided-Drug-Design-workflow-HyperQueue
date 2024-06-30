import dataclasses
import enum
from pathlib import Path

from ...wrapper.gromacs import Gromacs

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
class AWHTools:
    gmx: Gromacs
