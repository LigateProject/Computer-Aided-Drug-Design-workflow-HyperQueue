from ..utils.paths import GenericPath
from ..utils.text import line_as_numbers
from .pose import Pose


def construct_additional_gromacs_files(
    pose: Pose,
    pose_number: int,
    gromacs_input: GenericPath,
    gromacs_output: GenericPath,
):
    """
    Constructs a .gro file from the provided pose and Gromacs input file.
    The `pose_number` will be stored as into the file.
    `pose_number` should start from 1.
    """
    assert pose_number >= 1

    coordinates = []
    for mol_line in pose.atoms.lines:
        values = line_as_numbers(mol_line, [2, 3, 4], float)
        values = [v / 10.0 for v in values]
        coordinates.append(values)

    with open(gromacs_input) as gromacs_in:
        with open(gromacs_output, "w") as gromacs_out:
            lines = gromacs_in.readlines()
            counter = -1
            for line in lines:
                if counter > 0:
                    line_list = line.split()
                    if line == lines[-1]:
                        gromacs_out.write(line)
                        break
                    else:
                        string = ""
                        for i in range(3):
                            string += line_list[i].rjust(5)
                        string += line_list[3].rjust(5)
                        for i in range(3):
                            string += f"{coordinates[counter - 1][i]:8.3f}"
                        string += "\n"
                        gromacs_out.write(string)
                elif counter == 0:
                    gromacs_out.write(line)
                else:
                    gromacs_out.write(f"Ligand pose {pose_number:5d}\n")
                counter += 1


def shift_last_gromacs_line(path: GenericPath, value: float):
    """
    Shifts the numbers in the last line of the gro file at `path` by `value`.
    The change is performed in-place.
    """
    line_offset = 0
    line_content = ""
    with open(path) as f:
        # Find the starting offset of the last line
        for line in f:
            line_offset += len(line_content)
            line_content = line
    values = line_content.split()
    values = [float(v) + value for v in values]
    values = " ".join(f"{v:11.5f}" for v in values)

    with open(path, "r+") as f:
        f.truncate(line_offset)
        f.seek(line_offset)
        f.write(f"{values}\n")