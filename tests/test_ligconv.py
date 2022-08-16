import pytest

from ligate.forcefields import FF
from ligate.ligconv.pdb import convert_pdb_to_gmx
from ligate.ligconv.pose import (
    extract_and_clean_pose,
    extract_pose,
    load_poses,
    load_single_pose,
)
from ligate.ligconv.topology import (
    merge_topologies,
    pos_res_for_ligand_to_fix_structure,
)
from ligate.wrapper.gmx import GMX

from .conftest import data_path
from .utils.io import check_files_are_equal, remove_lines


def test_convert_pdb_to_gmx(gmx: GMX, tmpdir):
    pdb_path = data_path("ligen/p38/protein_amber/protein.pdb")
    convert_pdb_to_gmx(gmx, pdb_path, tmpdir)


def test_load_poses():
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )
    poses = list(load_poses(pose_path))
    assert len(poses) == 50
    assert list(range(1, 51)) == [pose.id for pose in poses]


def test_load_first_pose():
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )
    pose = load_single_pose(pose_path, 1)
    assert pose.id == 1
    assert len(pose.atoms.lines) == 43
    assert len(pose.molecule.lines) == 4
    assert len(pose.bonds.lines) == 45
    assert len(pose.substructure.lines) == 1
    assert pose.ligen_score == 5.061719


def test_load_last_pose():
    pose_path = data_path(
        "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    )
    pose = load_single_pose(pose_path, 50)
    assert pose.id == 50
    assert len(pose.atoms.lines) == 43
    assert len(pose.molecule.lines) == 4
    assert len(pose.bonds.lines) == 45
    assert len(pose.substructure.lines) == 1
    assert pose.ligen_score == 5.235692


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
    compare("out_gaff2/out.itp", "out_gaff2/out.itp", skip_lines=[0])
    compare("out_gaff2/out.top", "out_gaff2/out.top", skip_lines=[0])


def test_merge_topologies(tmpdir):
    root = data_path("ligen/p38/ligands_gaff2")

    topology = tmpdir / "topology.itp"
    structure = tmpdir / "structure.gro"

    merge_topologies(
        root / "lig_p38a_2aa/topology/ligand.itp",
        root / "lig_p38a_2aa/poses/1/ligand.mol2",
        root / "lig_p38a_2aa/poses/1/ligand.gro",
        root / "lig_p38a_2bb/topology/ligand.itp",
        root / "lig_p38a_2bb/poses/1/ligand.mol2",
        root / "lig_p38a_2bb/poses/1/ligand.gro",
        topology,
        structure,
    )
    check_files_are_equal(data_path("ligen/p38/fixtures/merged/topology.itp"), topology)
    check_files_are_equal(
        data_path("ligen/p38/fixtures/merged/structure.gro"), structure
    )


def test_posres_fix_structure(tmpdir):
    output = tmpdir / "out.itp"

    pos_res_for_ligand_to_fix_structure(
        data_path(
            "ligen/p38/ligands_gaff2/lig_p38a_2aa/edges/lig_p38a_2aa_p38a_2bb/topology"
            "/merged.itp"
        ),
        output,
    )
    check_files_are_equal(
        data_path(
            "ligen/p38/fixtures/edges/lig_p38a_2aa_p38a_2bb/topology/posre_Ligand.itp"
        ),
        output,
    )
