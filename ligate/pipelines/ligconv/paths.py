from pathlib import Path

from ...ligconv.common import ProteinForcefield
from ...utils.io import ensure_directory
from ...utils.paths import normalize_path


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

    def dir_path(self, path: Path) -> Path:
        """
        Returns a path to a subdirectory, making sure that it is created in the process if it
        didn't exist yet.
        """
        return ensure_directory(self.root / path)

    def file_path(self, path: Path) -> Path:
        """
        Returns a path to a file within this `self.root`.
        """
        return self.root / path


class ProteinDirProvider(PathProvider):
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
