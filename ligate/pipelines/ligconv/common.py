import dataclasses
from pathlib import Path
from typing import Dict, List

from hyperqueue.task.task import Task

from ...ligconv.common import LigandForcefield, ProteinForcefield
from ...utils.io import ensure_directory


@dataclasses.dataclass
class LigenOutputData:
    """
    Contains paths to files produced by LiGen.
    """

    # Input protein PDB file
    protein_file: Path
    # Directory containing the ligands
    ligand_dir: Path
    # Ligands produced by Ligen
    ligands: List[Path]

    def pose_file(self, ligand_name: str) -> Path:
        return self.ligand_dir / ligand_name / "out_amber_pose_000001.txt"

    def ligand_name(self, ligand: Path) -> str:
        return ligand.name


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
        return ensure_directory(
            self.protein_dir
            / edge_directory_name(edge)
            / self.protein_ff_name
            / "topology"
        )

    def edge_structure_dir(self, edge: Edge) -> Path:
        return ensure_directory(
            self.protein_dir
            / edge_directory_name(edge)
            / self.protein_ff_name
            / "structure"
        )

    def ligand_dir(self, ligand_name: str) -> Path:
        return ensure_directory(
            self.protein_dir / "ligands" / ligand_name / self.protein_ff_name
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

    def edge_topology_ligand_in_water(self, edge: Edge) -> Path:
        return self.edge_topology_dir(edge) / "topol_ligandInWater.top"

    def edge_merged_topology_gro(self, edge: Edge) -> Path:
        return self.edge_topology_dir(edge) / "merged.itp"


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"


@dataclasses.dataclass
class LigConvLigandTaskState:
    ligand_to_task: Dict[str, Task]

    def get_ligand_task(self, ligand_name: str) -> Task:
        return self.ligand_to_task[ligand_name]


@dataclasses.dataclass
class LigConvEdgeTaskState:
    edge_to_task: Dict[Edge, Task]

    def get_edge_task(self, edge: Edge) -> Task:
        return self.edge_to_task[edge]
