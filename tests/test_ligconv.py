import pytest

from ligate.ligconv.common import LigandForcefield
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
from ligate.utils.paths import use_dir
from ligate.wrapper.gmx import GMX

from .utils.io import check_files_are_equal, remove_lines


def test_convert_pdb_to_gmx(gmx: GMX, data_dir, tmp_path):
    pdb_path = data_dir / "ligen/p38/protein_amber/protein.pdb"
    convert_pdb_to_gmx(gmx, pdb_path, tmp_path)


def test_load_poses(data_dir):
    pose_path = data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    poses = list(load_poses(pose_path))
    assert len(poses) == 50
    assert list(range(1, 51)) == [pose.id for pose in poses]


def test_load_first_pose(data_dir):
    pose_path = data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    pose = load_single_pose(pose_path, 1)
    assert pose.id == 1
    assert len(pose.atoms.lines) == 43
    assert len(pose.molecule.lines) == 4
    assert len(pose.bonds.lines) == 45
    assert len(pose.substructure.lines) == 1
    assert pose.ligen_score == 5.061719


def test_load_last_pose(data_dir):
    pose_path = data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"
    pose = load_single_pose(pose_path, 50)
    assert pose.id == 50
    assert len(pose.atoms.lines) == 43
    assert len(pose.molecule.lines) == 4
    assert len(pose.bonds.lines) == 45
    assert len(pose.substructure.lines) == 1
    assert pose.ligen_score == 5.235692


@pytest.mark.parametrize("pose", (1, 2, 4))
def test_extract_and_clean_pose(pose: int, data_dir, tmp_path, babel):
    pose_path = data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2aa/out_amber_pose_000001.txt"

    output = tmp_path / "pose.mol2"
    extract_and_clean_pose(pose_path, pose, output, babel)
    check_files_are_equal(data_dir / f"ligen/p38/fixtures/pose{pose}-cleaned.mol2", output)


def test_extract_pose_with_dummy_atoms(data_dir, tmp_path):
    pose_path = data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2c/out_amber_pose_000001.txt"

    output = tmp_path / "pose.mol2"
    extract_pose(pose_path, 1, output)
    check_files_are_equal(data_dir / "ligen/p38/fixtures/pose-dummy-atoms.mol2", output)


def test_extract_pose_with_dummy_bonds(data_dir, tmp_path):
    pose_path = data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2c/out_amber_pose_000002.txt"

    output = tmp_path / "pose.mol2"
    extract_pose(pose_path, 1, output)
    check_files_are_equal(data_dir / "ligen/p38/fixtures/pose-dummy-bonds.mol2", output)


@pytest.mark.slow
def test_run_stage(data_dir, tmp_path, stage):
    input_path = data_dir / "ligen/p38/fixtures/pose1-cleaned.mol2"

    def compare(expected: str, actual: str, skip_lines=()):
        actual = tmp_path / actual
        if skip_lines:
            remove_lines(actual, lines=list(skip_lines))

        check_files_are_equal(data_dir / f"ligen/p38/fixtures/stage/{expected}", actual)

    with use_dir(tmp_path):
        output = tmp_path / "out"
        stage.run(input_path, str(output), LigandForcefield.Gaff2)

        compare("out.gro", "out.gro", skip_lines=[0])
        compare("out.mol2", "out.mol2")
        compare("posre_out.itp", "posre_out.itp")
        compare("out_gaff2/out.itp", "out_gaff2/out.itp", skip_lines=[0])
        compare("out_gaff2/out.top", "out_gaff2/out.top", skip_lines=[0])


def test_merge_topologies(data_dir, tmp_path):
    root = data_dir / "ligen/p38/ligands_gaff2"

    topology = tmp_path / "topology.itp"
    structure = tmp_path / "structure.gro"

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
    check_files_are_equal(data_dir / "ligen/p38/fixtures/merged/topology.itp", topology)
    check_files_are_equal(data_dir / "ligen/p38/fixtures/merged/structure.gro", structure)


def test_posres_fix_structure(data_dir, tmp_path):
    output = tmp_path / "out.itp"

    pos_res_for_ligand_to_fix_structure(
        data_dir / "ligen/p38/ligands_gaff2/lig_p38a_2aa/edges/lig_p38a_2aa_p38a_2bb/topology"
        "/merged.itp",
        output,
    )
    check_files_are_equal(
        data_dir / "ligen/p38/fixtures/edges/lig_p38a_2aa_p38a_2bb/topology/posre_Ligand.itp",
        output,
    )
