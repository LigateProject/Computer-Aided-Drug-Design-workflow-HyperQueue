import dataclasses
from pathlib import Path

from ...utils.io import ensure_directory
from ...utils.paths import normalize_path
from .common import Edge, LigConvParameters, LigConvTools, LigenOutputData
from .paths import LigConvProteinDir


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
    def protein_dir(self) -> LigConvProteinDir:
        # TODO: change to some general name, like protein
        return LigConvProteinDir(self.workdir / "p38", self.params.protein_ff)

    @property
    def protein_dir_legacy(self) -> Path:
        return ensure_directory(self.workdir / "p38")

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


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"
