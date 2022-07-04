from ligate.gmx import GMX
from ligate.ligconv.pdb import convert_pdb_to_gmx

from .conftest import data_path


def test_convert_pdb_to_gmx(gmx: GMX, tmpdir):
    pdb_path = data_path("ligen/p38/protein_amber/protein.pdb")
    convert_pdb_to_gmx(gmx, pdb_path, tmpdir)
