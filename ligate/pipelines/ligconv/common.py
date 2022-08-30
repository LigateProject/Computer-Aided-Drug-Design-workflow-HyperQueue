import dataclasses
from pathlib import Path
from typing import List

from ...ligconv.common import LigandForcefield, ProteinForcefield
from ...utils.paths import normalize_path
from ...wrapper.babel import Babel
from ...wrapper.gmx import GMX
from ...wrapper.stage import Stage


@dataclasses.dataclass
class LigenOutputData:
    """
    Contains paths to files produced by LiGen.
    """

    # Input protein PDB file
    protein_file: Path
    # Directory containing the ligands
    ligand_dir: Path

    def __post_init__(self):
        self.protein_file = normalize_path(self.protein_file)
        self.ligand_dir = normalize_path(self.ligand_dir)

    def pose_file(self, ligand_name: str) -> Path:
        return self.ligand_path(ligand_name) / "out_amber_pose_000001.txt"

    def ligand_name(self, ligand: Path) -> str:
        return ligand.name

    def ligand_path(self, ligand_name: str) -> Path:
        return self.ligand_dir / ligand_name

    def has_ligand(self, ligand_name: str) -> bool:
        return self.ligand_path(ligand_name).is_dir()


@dataclasses.dataclass(frozen=True)
class Edge:
    """
    An edge between two ligands.
    """

    start_ligand: str
    end_ligand: str

    def start_ligand_name(self) -> str:
        return f"lig_{self.start_ligand}"

    def end_ligand_name(self) -> str:
        return f"lig_{self.end_ligand}"

    def name(self) -> str:
        return f"{self.start_ligand}-{self.end_ligand}"


@dataclasses.dataclass
class LigConvParameters:
    """
    Parameters for converting ligen output data to edges that can be handled by AWH.
    """

    protein_ff: ProteinForcefield
    ligand_ff: LigandForcefield
    edges: List[Edge]


@dataclasses.dataclass
class LigConvTools:
    """
    Tools required to perform the LigConv pipeline.
    """

    gmx: GMX
    babel: Babel
    stage: Stage
