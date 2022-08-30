import dataclasses
from pathlib import Path
from typing import List

from .paths import ProteinDirProvider
from ...ligconv.common import LigandForcefield, ProteinForcefield
from ...utils.io import ensure_directory
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


@dataclasses.dataclass
class LigConvContext:
    """
    Context that holds all required inputs and tools for the LigConv pipeline.
    Based on `workdir`, it provides paths to various file locations.
    """
    tools: LigConvTools
    ligen_data: LigenOutputData
    params: LigConvParameters
    workdir: Path

    def __post_init__(self):
        self.workdir = ensure_directory(normalize_path(self.workdir))

    @property
    def protein_ff_name(self) -> str:
        return self.params.protein_ff.to_str()

    # Paths
    @property
    def protein_dir(self) -> ProteinDirProvider:
        # TODO: change to some general name, like protein
        return ProteinDirProvider(self.workdir / "p38", self.params.protein_ff)

    @property
    def protein_dir_legacy(self) -> Path:
        return ensure_directory(self.workdir / "p38")

    def edge_dir(self, edge: Edge) -> Path:
        return ensure_directory(
            self.protein_dir_legacy / edge_directory_name(edge) / self.protein_ff_name
        )

    def edge_topology_dir(self, edge: Edge) -> Path:
        return self.edge_dir(edge) / "topology"

    def edge_structure_dir(self, edge: Edge) -> Path:
        return self.edge_dir(edge) / "structure"

    def ligand_dir(self, ligand_name: str) -> Path:
        return ensure_directory(
            self.protein_dir_legacy / "ligands" / ligand_name / self.protein_ff_name
        )

    def ligand_topology_dir(self, ligand_name: str) -> Path:
        return ensure_directory(self.ligand_dir(ligand_name) / "topology")

    def ligand_topology_itp(self, ligand_name: str) -> Path:
        return self.ligand_topology_dir(ligand_name) / "ligand.itp"

    def ligand_pose_dir(self, ligand_name: str, pose_id: int) -> Path:
        return ensure_directory(self.ligand_dir(ligand_name) / "poses" / str(pose_id))

    def ligand_pose_structure_gro(self, ligand: str, pose_id: int) -> Path:
        return self.ligand_pose_dir(ligand, pose_id) / "ligand.gro"

    def ligand_pose_structure_mol2(self, ligand: str, pose_id: int) -> Path:
        return self.ligand_pose_dir(ligand, pose_id) / "ligand.mol2"

    def edge_merged_structure_gro(self, edge: Edge) -> Path:
        return self.edge_structure_dir(edge) / "merged.gro"

    def edge_full_structure_gro(self, edge: Edge) -> Path:
        return self.edge_structure_dir(edge) / "full.gro"

    def edge_topology_ligand_in_water(self, edge: Edge) -> Path:
        return self.edge_topology_dir(edge) / "topol_ligandInWater.top"

    def edge_merged_topology_gro(self, edge: Edge) -> Path:
        return self.edge_topology_dir(edge) / "merged.itp"


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"
