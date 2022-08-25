from ...utils.io import ensure_directory
from ...utils.paths import GenericPath, normalize_path
from .common import LigConvContext, LigConvParameters, LigenOutputData


def load_ligen_output_data(
    protein_file: GenericPath, ligand_dir: GenericPath
) -> LigenOutputData:
    """
    Loads Ligen data from a Ligen output directory.
    """
    ligand_dir = normalize_path(ligand_dir)
    return LigenOutputData(
        protein_file=normalize_path(protein_file),
        ligand_dir=ligand_dir,
    )


def prepare_ligconv_directories(
    ligen_data: LigenOutputData,
    workdir: GenericPath,
    params: LigConvParameters,
) -> LigConvContext:
    """
    Performs a sanity check and prepares directories for the AWH pipeline into `workdir`.
    """
    for edge in params.edges:
        missing = []
        start = edge.start_ligand_name()
        if not ligen_data.has_ligand(start):
            missing.append(start)
        end = edge.end_ligand_name()
        if not ligen_data.has_ligand(end):
            missing.append(end)
        if missing:
            raise Exception(f"{edge} links ligand(s) that were not found: {missing}")

    workdir = ensure_directory(workdir)
    return LigConvContext(ligen_data=ligen_data, params=params, workdir=workdir)
