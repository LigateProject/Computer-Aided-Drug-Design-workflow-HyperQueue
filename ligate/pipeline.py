import dataclasses
import enum
import shutil
from pathlib import Path
from typing import List

from .forcefields import FF, Forcefield
from .utils.io import (
    GenericPath,
    check_dir_exists,
    ensure_directory,
    iterate_directories,
    normalize_path,
)
from .utils.paths import use_dir
from .wrapper.gmx import GMX


@dataclasses.dataclass
class LigenOutputData:
    protein: str
    protein_file: Path
    ligand_dir: Path
    protein_ff_dir: Path
    ligands: List[Path]


def load_ligen_data(
    ligen_output_dir: GenericPath,
    protein: str,
    ligand: str,
    protein_file: str,
    protein_forcefield: str,
) -> LigenOutputData:
    """
    Loads data from a Ligen output directory.

    :param ligen_output_dir: Output directory produced by Ligen.
    :param protein: Name of the protein (e.g. `p38`).
    :param ligand: Name of the ligand (e.g. `ligands_gaff2`).
    :param protein_file: Protein file (e.g. `protein.pdb`).
    :param protein_forcefield: Name of the forcefield (e.g. `protein_amber`).
    """
    ligen_protein_dir = normalize_path(ligen_output_dir) / protein
    check_dir_exists(ligen_protein_dir)

    ligand_dir = ligen_protein_dir / ligand
    check_dir_exists(ligand_dir)
    protein_ff_dir = ligen_protein_dir / protein_forcefield
    check_dir_exists(protein_ff_dir)

    protein_file = protein_ff_dir / protein_file

    ligands = iterate_directories(ligand_dir)
    return LigenOutputData(
        protein=protein,
        ligand_dir=ligand_dir,
        protein_ff_dir=protein_ff_dir,
        ligands=ligands,
        protein_file=protein_file,
    )


@dataclasses.dataclass
class PipelineConfiguration:
    forcefield: Forcefield
    FF: FF
    pose_number: int
    edges: List[str]


@dataclasses.dataclass
class PreparedWorkdir:
    ligen_data: LigenOutputData
    configuration: PipelineConfiguration
    workdir: Path

    # Paths
    @property
    def protein_dir(self) -> Path:
        return self.workdir / self.ligen_data.protein

    @property
    def protein_topology_dir(self) -> Path:
        return self.protein_dir / self.forcefield_name / "topology"

    @property
    def protein_structure_dir(self) -> Path:
        return self.protein_dir / self.forcefield_name / "structure"

    def edge_topology_dir(self, edge: str) -> Path:
        return self.protein_dir / edge / self.forcefield_name / "topology"

    def edge_structure_dir(self, edge: str) -> Path:
        return self.protein_dir / edge / self.forcefield_name / "structure"

    @property
    def forcefield_name(self) -> str:
        return self.configuration.forcefield.to_str()


def prepare_directories(
    ligen_data: LigenOutputData,
    workdir: GenericPath,
    configuration: PipelineConfiguration,
) -> PreparedWorkdir:
    """
    Prepares directories for the AWH pipeline into `workdir`.
    """
    workdir = ensure_directory(workdir)
    protein_dir = ensure_directory(workdir / ligen_data.protein)

    ff_dir = ensure_directory(protein_dir / configuration.forcefield.to_str())
    ensure_directory(ff_dir / "topology")
    ensure_directory(ff_dir / "structure")

    ligands_dir = ensure_directory(protein_dir / "ligands")
    for ligand in ligen_data.ligands:
        ligand_name = ligand.name
        ligand_dir = ensure_directory(ligands_dir / ligand_name)
        ff_dir = ensure_directory(ligand_dir / configuration.FF.to_str())
        ensure_directory(ff_dir / "topology")
        ensure_directory(ff_dir / "poses")
        ensure_directory(ff_dir / "poses" / str(configuration.pose_number))

    for edge in configuration.edges:
        edge_dir = ensure_directory(protein_dir / edge)
        ff_dir = ensure_directory(edge_dir / configuration.forcefield.to_str())
        ensure_directory(ff_dir / "topology")
        ensure_directory(ff_dir / "structure")
    return PreparedWorkdir(
        ligen_data=ligen_data, configuration=configuration, workdir=workdir
    )


class ProteinTopologyForcefield(enum.Enum):
    Amber99SB_ILDN = 6


class ProteinTopologyWaterModel(enum.Enum):
    Tip3p = 1


@dataclasses.dataclass
class ProteinTopologyParams:
    forcefield: ProteinTopologyForcefield
    water_model: ProteinTopologyWaterModel


def create_protein_topology(
    gmx: GMX, prepared: PreparedWorkdir, params: ProteinTopologyParams
):
    with use_dir(prepared.protein_topology_dir):
        gmx.execute(
            ["pdb2gmx", "-f", prepared.ligen_data.protein_file, "-renum", "-ignh"],
            input=f"{params.forcefield.value}\n{params.water_model.value}".encode(),
        )
        shutil.move("conf.gro", prepared.protein_structure_dir)
    # Copy protein topology and structure to all edges
    for edge in prepared.configuration.edges:
        shutil.copytree(
            prepared.protein_topology_dir,
            prepared.edge_topology_dir(edge),
            dirs_exist_ok=True,
        )
        shutil.copytree(
            prepared.protein_structure_dir,
            prepared.edge_structure_dir(edge),
            dirs_exist_ok=True,
        )
