import pytest

from ligate.forcefields import FF
from ligate.ligconv.gromacs import construct_additional_gromacs_files
from ligate.ligconv.pdb import convert_pdb_to_gmx
from ligate.ligconv.pose import extract_and_clean_pose, extract_pose, load_single_pose
from ligate.wrapper.gmx import GMX

from .conftest import data_path
from .utils.io import check_files_are_equal, remove_lines


def test_convert_pdb_to_gmx(gmx: GMX, tmpdir):
    pdb_path = data_path("ligen/p38/protein_amber/protein.pdb")
    convert_pdb_to_gmx(gmx, pdb_path, tmpdir)


@pytest.mark.parametrize("pose", (1, 2, 4))
def test_extract_and_clean_pose(pose: int, tmpdir, babel):
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )

    output = tmpdir / "pose.mol2"
    extract_and_clean_pose(pose_path, pose, output, babel)
    check_files_are_equal(
        data_path(f"ligen/p38/fixtures/pose{pose}-cleaned.mol2"), output
    )


def test_extract_pose_with_dummy_atoms(tmpdir):
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2c/out_amber_pose_000001.txt"
    )

    output = tmpdir / "pose.mol2"
    extract_pose(pose_path, 1, output)
    check_files_are_equal(data_path("ligen/p38/fixtures/pose-dummy-atoms.mol2"), output)


def test_extract_pose_with_dummy_bonds(tmpdir):
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2c/out_amber_pose_000002.txt"
    )

    output = tmpdir / "pose.mol2"
    extract_pose(pose_path, 1, output)
    check_files_are_equal(data_path("ligen/p38/fixtures/pose-dummy-bonds.mol2"), output)


def test_run_stage(tmpdir, stage):
    input_path = data_path("ligen/p38/fixtures/pose1-cleaned.mol2")

    def compare(expected: str, actual: str, skip_lines=()):
        actual = tmpdir / actual
        if skip_lines:
            remove_lines(actual, lines=list(skip_lines))

        check_files_are_equal(data_path(f"ligen/p38/fixtures/stage/{expected}"), actual)

    output = tmpdir / "out"
    stage.run(input_path, str(output), FF.Gaff2)

    compare("out.gro", "out.gro", skip_lines=[0])
    compare("out.mol2", "out.mol2")
    compare("posre_out.itp", "posre_out.itp")
    compare("out_gaff/out.itp", "out_gaff/out.itp", skip_lines=[0])
    compare("out_gaff/out.top", "out_gaff/out.top", skip_lines=[0])


def test_construct_additional_gromacs_files(tmpdir):
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )
    pose = load_single_pose(pose_path, 0)
    gro_path = data_path("ligen/p38/ligands_gaff2/lig_p38a_2aa/mol_gmx_stage.gro")

    out_path = tmpdir / "out.gro"
    construct_additional_gromacs_files(pose, 1, gro_path, out_path)
    check_files_are_equal(
        data_path("ligen/p38/fixtures/gromacs/lig_p38a_2aa_additional.gro"), out_path
    )
