import dataclasses
import itertools
import tempfile
from typing import List

from ..utils.io import GenericPath, delete_file
from ..utils.text import line_as_numbers
from ..wrapper.babel import Babel


@dataclasses.dataclass
class PoseSection:
    header: str
    lines: List[str]


@dataclasses.dataclass
class Pose:
    molecule: PoseSection
    atoms: PoseSection
    bonds: PoseSection
    substructure: PoseSection


def split_by_prefix(lines: List[str], prefix: str) -> List[PoseSection]:
    data = []
    for line in lines:
        if line.startswith(prefix):
            data.append(PoseSection(line, []))
        else:
            data[-1].lines.append(line)
    return data


def iterate_poses(file):
    pose_lines = []

    reading_pose = False
    for line in file:
        if reading_pose:
            if not line.strip() or line.startswith("#"):
                yield list(pose_lines)
                reading_pose = False
                pose_lines.clear()
                continue
        elif "@<TRIPOS>" in line:
            reading_pose = True
        else:
            continue
        pose_lines.append(line.rstrip())
    if pose_lines:
        yield list(pose_lines)


def parse_pose(lines: List[str]) -> Pose:
    lines = [line.rstrip() for line in lines]
    molecule, atoms, bonds, substructure = split_by_prefix(lines, "@<TRIPOS>")
    atom_count, bond_count = line_as_numbers(molecule.lines[1], [0, 1])
    assert atom_count == len(atoms.lines)
    assert bond_count == len(bonds.lines)

    # Filter dummy atoms
    dummy_atoms = set()
    valid_atom_lines = []
    for atom in atoms.lines:
        if "Du" in atom:
            dummy_atoms.add(line_as_numbers(atom, [0])[0])
        else:
            valid_atom_lines.append(atom)

    # Filter bonds containing dummy atoms
    valid_bond_lines = []
    for bond in bonds.lines:
        atom_a, atom_b = line_as_numbers(bond, [1, 2])
        if atom_a not in dummy_atoms and atom_b not in dummy_atoms:
            valid_bond_lines.append(bond)

    return Pose(
        molecule=molecule,
        atoms=PoseSection(atoms.header, valid_atom_lines),
        bonds=PoseSection(bonds.header, valid_bond_lines),
        substructure=substructure,
    )


def join_lines(lines: List[str], separator="\n") -> str:
    return separator.join(lines)


def load_single_pose(path: GenericPath, pose_number: int) -> Pose:
    """
    Loads a single pose from the file at `path`.
    `pose_number` is numbered from zero.
    """
    with open(path) as file:
        pose_data = next(
            itertools.islice(iterate_poses(file), pose_number, pose_number + 1)
        )
    return parse_pose(pose_data)


# Extracts pose data to a mol2 file
def extract_pose(pose_file: GenericPath, pose_number: int, output: GenericPath):
    """
    Extract a single pose with the given number (index starting from 1) from the `pose_file`.
    Writes the pose into `output`.

    The poses file is also cleaned with Babel.
    """
    assert pose_number >= 1
    pose = load_single_pose(pose_file, pose_number - 1)

    with open(output, "w") as file:
        # Write molecule header
        file.write(f"{pose.molecule.header}\n")
        file.write(f"{pose.molecule.lines[0]}\n")

        nums = line_as_numbers(pose.molecule.lines[1], [0, 1, 2, 3, 4])
        file.write(
            f"{len(pose.atoms.lines):5} {len(pose.bonds.lines):5} "
            f"{nums[2]:5} {nums[3]:5} {nums[4]:5}\n"
        )
        file.write(f"{join_lines(pose.molecule.lines[2:])}\n")

        # Write atoms
        file.write(f"{pose.atoms.header}\n")
        file.write(f"{join_lines(pose.atoms.lines)}\n")

        # Write bonds
        file.write(f"{pose.bonds.header}\n")
        file.write(f"{join_lines(pose.bonds.lines)}\n")

        # Write substructure
        file.write(f"{pose.substructure.header}\n")
        file.write(f"{join_lines(pose.substructure.lines)}\n")


def extract_and_clean_pose(
    pose_file: GenericPath, pose_number: int, output: GenericPath, babel: Babel
):
    """
    Extract a single pose with the given number (index starting from 1) from the `pose_file`.
    Writes the pose into `output`.

    The poses file is also cleaned with Babel.
    """
    assert pose_number >= 1
    with tempfile.NamedTemporaryFile(suffix=".mol2") as tmpfile:
        temp_pose_file = tmpfile.name
        extract_pose(pose_file, pose_number, temp_pose_file)
        babel.normalize_mol2(temp_pose_file, output)
