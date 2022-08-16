import shutil

from ligate.ligconv.gromacs import (
    construct_additional_gromacs_files,
    shift_last_gromacs_line,
)
from ligate.ligconv.pose import load_single_pose

from .conftest import data_path
from .utils.io import check_files_are_equal


def test_construct_additional_gromacs_files(tmpdir):
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )
    pose = load_single_pose(pose_path, 1)
    gro_path = data_path("ligen/p38/ligands_gaff2/lig_p38a_2aa/mol_gmx_stage.gro")

    out_path = tmpdir / "out.gro"
    construct_additional_gromacs_files(pose, 1, gro_path, out_path)
    check_files_are_equal(
        data_path("ligen/p38/fixtures/gromacs/lig_p38a_2aa_additional.gro"), out_path
    )


def test_shift_last_gromacs_line(tmpdir):
    path = tmpdir / "merged.gro"
    shutil.copy(
        data_path(
            "ligen/p38/ligands_gaff2/lig_p38a_2aa/edges/lig_p38a_2aa_p38a_2bb/structure/merged.gro"
        ),
        path,
    )

    shift_last_gromacs_line(path, 10)
    check_files_are_equal(
        data_path(
            "ligen/p38/fixtures/edges/lig_p38a_2aa_p38a_2bb/structure/merged-shifted-10.gro"
        ),
        path,
    )
