import dataclasses
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


@dataclasses.dataclass
class LigenOutputData:
    protein: str
    ligand_dir: Path
    protein_ff_dir: Path
    ligands: List[Path]


def load_ligen_data(
    ligen_output_dir: GenericPath, protein: str, ligand: str, protein_forcefield: str
) -> LigenOutputData:
    """
    Loads data from a Ligen output directory.

    :param ligen_output_dir: Output directory produced by Ligen.
    :param protein: Name of the protein (e.g. `p38`).
    :param ligand: Name of the ligand (e.g. `ligands_gaff2`).
    :param protein_forcefield: Name of the forcefield (e.g. `protein_amber`).
    """
    ligen_protein_dir = normalize_path(ligen_output_dir) / protein
    check_dir_exists(ligen_protein_dir)

    ligand_dir = ligen_protein_dir / ligand
    check_dir_exists(ligand_dir)
    protein_ff_dir = ligen_protein_dir / protein_forcefield
    check_dir_exists(protein_ff_dir)

    ligands = iterate_directories(ligand_dir)
    return LigenOutputData(
        protein=protein,
        ligand_dir=ligand_dir,
        protein_ff_dir=protein_ff_dir,
        ligands=ligands,
    )


@dataclasses.dataclass
class PipelineConfiguration:
    forcefield: Forcefield
    FF: FF
    pose_number: int
    edges: List[str]


def prepare_directories(
    ligen_data: LigenOutputData,
    workdir: GenericPath,
    configuration: PipelineConfiguration,
):
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
