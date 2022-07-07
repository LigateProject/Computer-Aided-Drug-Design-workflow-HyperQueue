import itertools
import tempfile

from ..utils.io import GenericPath, delete_file
from ..wrapper.babel import Babel


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


# Extracts pose data to a mol2 file
def extract_pose(pose_file: GenericPath, pose_number: int, output: GenericPath):
    """
    Extract a single pose with the given number (index starting from 0) from the `pose_file`.
    Writes the pose into `output`.

    The poses file is also cleaned with Babel.
    """
    with open(pose_file) as file:
        pose_data = list(
            itertools.islice(iterate_poses(file), pose_number, pose_number + 1)
        )
        assert pose_data

    with open(output, "w") as file:
        for line in pose_data[0]:
            file.write(f"{line}\n")

    """
    with open(pose_file) as file:
        forbiddenLines = []
        forbiddenNumbers = []
        forbiddenAtoms = 0
        forbiddenBonds = 0
        count = 0.0
        for line in file:
            if "<TRIPOS>" in line:
                count += 1.0
            if (count / 4.0 > pose_number - 1) and (count / 4.0 < pose_number):
                lineToTest = line.split()
                # check atoms
                if "Du" in lineToTest:
                    forbiddenNumbers.append(lineToTest[0])
                    forbiddenLines.append(line)
                    forbiddenAtoms += 1
                # check bonds
                if (len(lineToTest) > 2) and (lineToTest[1] in forbiddenNumbers
                or lineToTest[2] in forbiddenNumbers):
                    forbiddenLines.append(line)
                    forbiddenBonds += 1

    file.seek(0)

    with open(output, "w") as output_file:
        # let's hope babel doesn't require atom numbering in MOL2 files to be continuous
        count = 0.0
        for line in file:
            if "<TRIPOS>" in line:
                count += 1.0
            if (count/4.0 > intNumber-1) and (count/4.0 < intNumber):
                if line not in forbiddenLines:
                    # correct header
                    lineToTest = line.split()
                    if (lineToTest[0] in forbiddenNumbers) and (len(lineToTest) == 5):
                        output_file.write("%5d %5d %5d %5d %5d\n" %
                        (int(lineToTest[0])-forbiddenAtoms,
                        int(lineToTest[1])-forbiddenBonds,
                        int(lineToTest[2]), int(lineToTest[3]), int(lineToTest[4])))
                        continue
                    output_file.write(line)
            elif count/4.0 == intNumber:
                if (line.find("#") == -1) and (len(line.split()) > 0):
                    output_file.write(line)"""


def extract_and_clean_pose(
    pose_file: GenericPath, pose_number: int, output: GenericPath, babel: Babel
):
    """
    Extract a single pose with the given number (index starting from 0) from the `pose_file`.
    Writes the pose into `output`.

    The poses file is also cleaned with Babel.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mol2") as tmpfile:
        temp_pose_file = tmpfile.name
    extract_pose(pose_file, pose_number, temp_pose_file)
    babel.normalize_mol2(temp_pose_file, output)
    delete_file(temp_pose_file)
