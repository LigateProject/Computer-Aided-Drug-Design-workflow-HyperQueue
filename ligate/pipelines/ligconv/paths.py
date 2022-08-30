from pathlib import Path

from ...ligconv.common import ProteinForcefield
from ...utils.io import ensure_directory
from ...utils.paths import GenericPath, normalize_path
from .common import Edge


class PathProvider:
    """
    Class that represents a directory containing experiment files.
    Provides paths to various components.
    """

    def __init__(self, root: Path):
        self.root = ensure_directory(normalize_path(root))

    @property
    def path(self) -> Path:
        return self.root

    def dir_path(self, path: GenericPath) -> Path:
        """
        Returns a path to a subdirectory, making sure that it is created in the process if it
        didn't exist yet.
        """
        return ensure_directory(self.root / path)

    def file_path(self, path: GenericPath) -> Path:
        """
        Returns a path to a file within this `self.root`.
        """
        file_path = self.root / path
        ensure_directory(file_path.parent)
        return file_path


class LigConvProteinDir(PathProvider):
    """
    Directory containing ligconv output for a specific protein and forcefield.
    """

    def __init__(self, root: Path, forcefield: ProteinForcefield):
        super().__init__(root)
        self.forcefield = forcefield

    @property
    def forcefield_name(self) -> str:
        return self.forcefield.to_str()

    @property
    def topology_dir(self) -> Path:
        return self.dir_path(Path(self.forcefield_name) / "topology")

    @property
    def structure_dir(self) -> Path:
        return self.dir_path(Path(self.forcefield_name) / "structure")

    def edge_dir(self, edge: Edge) -> "LigConvEdgeDir":
        """
        Return a provider for files that concern the given edge.
        """
        return LigConvEdgeDir(
            self.dir_path(Path(edge_directory_name(edge)) / self.forcefield_name)
        )

    def ligand_dir(self, ligand_name: str) -> "LigConvLigandDir":
        return LigConvLigandDir(
            self.dir_path(Path("ligands") / ligand_name / self.forcefield_name)
        )


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"


class LigConvEdgeDir(PathProvider):
    @property
    def topology_dir(self) -> Path:
        return self.dir_path("topology")

    @property
    def merged_topology_itp(self) -> Path:
        return self.topology_dir / "merged.itp"

    @property
    def topology_ligand_in_water(self) -> Path:
        return self.topology_dir / "topol_ligandInWater.top"

    @property
    def structure_dir(self) -> Path:
        return self.dir_path("structure")

    @property
    def merged_structure_gro(self) -> Path:
        return self.structure_dir / "merged.gro"

    @property
    def full_structure_gro(self) -> Path:
        return self.structure_dir / "full.gro"


class LigConvLigandDir(PathProvider):
    @property
    def topology_dir(self) -> Path:
        return self.dir_path("topology")

    @property
    def topology_itp(self) -> Path:
        return self.topology_dir / "ligand.itp"

    def pose_dir(self, pose_id: int) -> "LigConvPoseDir":
        return LigConvPoseDir(self.dir_path(Path("poses") / str(pose_id)))


class LigConvPoseDir(PathProvider):
    @property
    def structure_gro(self) -> Path:
        return self.file_path("ligand.gro")

    @property
    def structure_mol2(self) -> Path:
        return self.file_path("ligand.mol2")
