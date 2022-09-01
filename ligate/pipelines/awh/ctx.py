import dataclasses
from pathlib import Path

from ...ligconv.common import ProteinForcefield
from ...utils.io import copy_directory, ensure_directory
from ..ligconv.providers import LigConvEdgeDir
from .common import AWHTools
from .providers import AWHEdgeDir, AWHOutputDir


@dataclasses.dataclass
class AWHContext:
    @staticmethod
    def from_ligconv_edge_dir(
        tools: AWHTools,
        edge_dir: LigConvEdgeDir,
        protein_ff: ProteinForcefield,
        workdir: Path,
    ):
        """
        Copies the LigConv edge directory to `workdir` and creates an AWH computational context.
        """
        edge = edge_dir.edge
        target_edge_dir = workdir / f"edge_{edge.start_ligand}_{edge.end_ligand}"
        copy_directory(edge_dir.path, target_edge_dir)
        return AWHContext(
            tools=tools,
            edge_dir=AWHEdgeDir(target_edge_dir, edge_dir.edge),
            protein_forcefield=protein_ff,
            workdir=workdir,
        )

    tools: AWHTools
    # Edge output directory produced by LiGen-GROMACS conversion pipeline
    edge_dir: AWHEdgeDir
    # Protein forcefield used to generate the ligands
    protein_forcefield: ProteinForcefield
    # Directory with structure and topology of the input
    workdir: Path

    def __post_init__(self):
        self.workdir = ensure_directory(self.workdir)

    @property
    def output_dir(self) -> AWHOutputDir:
        return AWHOutputDir(self.workdir)

    def edge_name(self) -> str:
        return self.edge_dir.edge.name()
