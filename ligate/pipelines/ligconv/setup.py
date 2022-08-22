from pathlib import Path

from . import LigConvContext, LigConvParameters, LigenOutputData
from ...utils.io import ensure_directory, iterate_directories
from ...utils.paths import GenericPath, normalize_path


def load_ligen_output_data(
        protein_file: GenericPath,
        ligand_dir: GenericPath
) -> LigenOutputData:
    """
    Loads Ligen data from a Ligen output directory.
    """
    ligands = iterate_directories(ligand_dir)
    return LigenOutputData(
        protein_file=normalize_path(protein_file),
        ligands=ligands,
    )


def prepare_ligconv_directories(
        ligen_data: LigenOutputData,
        workdir: GenericPath,
        params: LigConvParameters,
) -> LigConvContext:
    """
    Performs a sanity check and prepares directories for the AWH pipeline into `workdir`.
    """
    ligand_names = [ligen_data.ligand_name(ligand) for ligand in ligen_data.ligands]
    for edge in params.edges:
        missing = []
        if edge.start_ligand_name() not in ligand_names:
            missing.append(edge.start_ligand_name())
        if edge.end_ligand_name() not in ligand_names:
            missing.append(edge.end_ligand_name())
        if missing:
            raise Exception(f"{edge} links ligand(s) that were not found: {missing}")

    workdir = ensure_directory(workdir)
    return LigConvContext(
        ligen_data=ligen_data,
        params=params,
        workdir=workdir
    )
