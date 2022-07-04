from ..gmx import GMX
from ..utils.io import GenericPath


def convert_pdb_to_gmx(gmx: GMX, pdb_path: GenericPath, gmx_path: GenericPath):
    """
    TODO: generalize
    AMBER99SB-ILDN - 6
    TIP3P - 1
    """
    gmx.execute(["pdb2gmx", "-f", pdb_path, "-renum", "-ignh"], input=b"6\n1")
