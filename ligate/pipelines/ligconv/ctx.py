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
    def protein_dir(self) -> LigConvProteinDir:
        # TODO: change to some general name, like protein
        return LigConvProteinDir(self.workdir / "p38", self.params.protein_ff)


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"
