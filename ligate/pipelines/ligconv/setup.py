from ...utils.io import ensure_directory
from ...utils.paths import GenericPath, normalize_path
from .common import LigConvContext, LigenOutputData


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


def sanity_check_ligconv(ctx: LigConvContext):
    """
    Performs a sanity check and prepares directories for the AWH pipeline into `workdir`.
    """
    for edge in ctx.params.edges:
        missing = []
        start = edge.start_ligand_name()
        if not ctx.ligen_data.has_ligand(start):
            missing.append(start)
        end = edge.end_ligand_name()
        if not ctx.ligen_data.has_ligand(end):
            missing.append(end)
        if missing:
            raise Exception(f"{edge} links ligand(s) that were not found: {missing}")

    ctx.workdir = ensure_directory(ctx.workdir)
