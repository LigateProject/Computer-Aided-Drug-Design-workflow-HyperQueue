from pathlib import Path

from ..utils.io import ensure_directory
from ..utils.paths import GenericPath


class PathProvider:
    """
    Class that represents a directory containing experiment files.
    Provides paths to various components.
    """

    def __init__(self, root: Path):
        self.root = ensure_directory(root)

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
