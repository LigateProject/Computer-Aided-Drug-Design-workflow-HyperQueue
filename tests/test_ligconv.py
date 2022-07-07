import pytest

from ligate.ligconv.pdb import convert_pdb_to_gmx
from ligate.ligconv.pose_extraction import extract_and_clean_pose
from ligate.wrapper.gmx import GMX

from .conftest import data_path
from .utils.io import check_files_are_equal


def test_convert_pdb_to_gmx(gmx: GMX, tmpdir):
    pdb_path = data_path("ligen/p38/protein_amber/protein.pdb")
    convert_pdb_to_gmx(gmx, pdb_path, tmpdir)


@pytest.mark.parametrize("pose", (0, 1, 3))
def test_extract_pose(pose: int, tmpdir, babel):
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )

    output = tmpdir / "pose.mol2"
    extract_and_clean_pose(pose_path, pose, output, babel)
    check_files_are_equal(data_path(f"ligen/p38/fixtures/pose{pose}.mol2"), output)
