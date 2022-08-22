import dataclasses
from pathlib import Path
from typing import List

from ...ligconv.common import LigandForcefield, ProteinForcefield
from ...utils.io import ensure_directory


@dataclasses.dataclass
class LigenOutputData:
    # Input protein PDB file
    protein_file: Path
    # Ligands produced by Ligen
    ligands: List[Path]

    def pose_file(self, ligand: Path) -> Path:
        return ligand / "out_amber_pose_000001.txt"

    def ligand_name(self, ligand: Path) -> str:
        return ligand.name


@dataclasses.dataclass
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


@dataclasses.dataclass
class LigConvParameters:
    """
    Parameters for converting ligen output data to edges that can be handled by AWH.
    """
    protein_ff: ProteinForcefield
    ligand_ff: LigandForcefield
    edges: List[Edge]


@dataclasses.dataclass
class LigConvContext:
    ligen_data: LigenOutputData
    params: LigConvParameters
    workdir: Path

    @property
    def protein_ff_name(self) -> str:
        return self.params.protein_ff.to_str()

    # Paths
    @property
    def protein_dir(self) -> Path:
        # TODO: change to some general name, like protein
        return ensure_directory(self.workdir / "p38")

    @property
    def protein_topology_dir(self) -> Path:
        return ensure_directory(self.protein_dir / self.protein_ff_name / "topology")

    @property
    def protein_structure_dir(self) -> Path:
        return ensure_directory(self.protein_dir / self.protein_ff_name / "structure")

    def edge_topology_dir(self, edge: Edge) -> Path:
        return (
                self.protein_dir
                / edge_directory_name(edge)
                / self.protein_ff_name
                / "topology"
        )

    def edge_structure_dir(self, edge: Edge) -> Path:
        return (
                self.protein_dir
                / edge_directory_name(edge)
                / self.protein_ff_name
                / "structure"
        )


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"
