import dataclasses
import itertools
import tempfile
from pathlib import Path
from typing import Iterable, List, Optional, TextIO

from ..utils.io import ensure_directory
from ..utils.paths import GenericPath
from ..utils.text import line_as_numbers
from ..wrapper.babel import Babel


@dataclasses.dataclass
class PoseSection:
    header: str
    lines: List[str]


@dataclasses.dataclass
class Pose:
    # 1-based pose ID
    id: int
    molecule: PoseSection
    atoms: PoseSection
    bonds: PoseSection
    substructure: PoseSection
    ligen_score: Optional[float]


def split_by_prefix(lines: Iterable[str], prefix: str) -> List[PoseSection]:
    data = []
    for line in lines:
        if line.startswith("#"):
            continue
        if line.startswith(prefix):
            data.append(PoseSection(line, []))
        else:
            data[-1].lines.append(line)
    return data


def read_pose_metadata(file: TextIO):
    for line in file:
        if line.startswith("#"):
            yield line.strip()
        else:
            break


def iterate_poses(file: TextIO) -> Iterable[List[str]]:
    """
    Goes through the input `file` and returns an iterator of pose lines.
    The lines of a pose include its header metadata and individual sections).
    """
    pose_lines = []

    while True:
        metadata = list(read_pose_metadata(file))
        if not metadata:
            return
        pose_lines.extend(metadata)
        for line in file:
            line = line.rstrip()
            if line.startswith("#ENDOFMOLECULE"):
                yield list(pose_lines)
                pose_lines.clear()
                break
            elif line:
                pose_lines.append(line)


def parse_pose(lines: List[str], pose_id: int) -> Pose:
    lines = [line.rstrip() for line in lines]

    metadata = {}

    # Parse metadata
    for line in lines:
        if line.startswith("#"):
            # Strip leading "# "
            line = line[2:].strip()
            key, value = line.split(":", maxsplit=1)
            key = key.strip()
            value = value.strip()
            metadata[key] = value
        else:
            break

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

    ligen_score = metadata.get("Ligen score")
    return Pose(
        id=pose_id,
        molecule=molecule,
        atoms=PoseSection(atoms.header, valid_atom_lines),
        bonds=PoseSection(bonds.header, valid_bond_lines),
        substructure=substructure,
        ligen_score=float(ligen_score) if ligen_score is not None else None,
    )


def join_lines(lines: List[str], separator="\n") -> str:
    return separator.join(lines)


def load_single_pose(path: GenericPath, pose_number: int) -> Pose:
    """
    Loads a single pose from the file at `path`.
    `pose_number` is numbered from one.
    """
    with open(path) as file:
        pose_data = next(itertools.islice(iterate_poses(file), pose_number - 1, pose_number))
    return parse_pose(pose_data, pose_number)


def load_poses(path: GenericPath) -> Iterable[Pose]:
    """
    Loads all poses from the file at `path`.
    """
    with open(path) as file:
        for pose_id, pose_data in enumerate(iterate_poses(file), start=1):
            yield parse_pose(pose_data, pose_id=pose_id)


# Extracts pose data to a mol2 file
def extract_pose(pose_file: GenericPath, pose_number: int, output: GenericPath):
    """
    Extract a single pose with the given number (index starting from 1) from the `pose_file`.
    Writes the pose into `output`.

    The poses file is also cleaned with Babel.
    """
    assert pose_number >= 1
    pose = load_single_pose(pose_file, pose_number)

    with open(output, "w") as file:
        # Write molecule header
        file.write(f"{pose.molecule.header}\n")
        file.write(f"{pose.molecule.lines[0]}\n")

        nums = line_as_numbers(pose.molecule.lines[1], [0, 1, 2, 3, 4])
        file.write(f"{len(pose.atoms.lines):5} {len(pose.bonds.lines):5} " f"{nums[2]:5} {nums[3]:5} {nums[4]:5}\n")
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


def extract_and_clean_pose(pose_file: GenericPath, pose_number: int, output: GenericPath, babel: Babel):
    """
    Extract a single pose with the given number (index starting from 1) from the `pose_file`.
    Writes the pose into `output`.

    The poses file is also cleaned with Babel.
    """
    assert pose_number >= 1
    with tempfile.NamedTemporaryFile(suffix=".mol2") as tmpfile:
        temp_pose_file = tmpfile.name
        extract_pose(pose_file, pose_number, temp_pose_file)

        ensure_directory(Path(output).parent)
        babel.normalize_mol2(temp_pose_file, output)
