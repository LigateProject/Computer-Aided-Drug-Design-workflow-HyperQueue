import difflib
import os
import shutil
from pathlib import Path
from typing import List

from ligate.utils.io import GenericPath

from ..conftest import BlessMode, get_bless_mode


def bless_file(expected: GenericPath, actual: GenericPath):
    os.makedirs(Path(expected).parent, exist_ok=True)
    shutil.copyfile(actual, expected)
    print(f"Blessing {expected} with {actual}")


def check_files_are_equal(expected: GenericPath, actual: GenericPath):
    try:
        expected_file = open(expected)
    except FileNotFoundError:
        if get_bless_mode().can_create():
            bless_file(expected, actual)
            return

        raise Exception(
            "Expected file `expected` not found. Run test again with BLESS=create to "
            "create it."
        )

    with open(actual) as actual_file:
        expected_file = expected_file.read()
        actual_file = actual_file.read()

        if expected_file != actual_file:
            if get_bless_mode() == BlessMode.Overwrite:
                bless_file(expected, actual)
                return

            error = f"{expected} and {actual} do not match\n"
            for line in difflib.unified_diff(
                expected_file.splitlines(),
                actual_file.splitlines(),
                fromfile=str(expected),
                tofile=str(actual),
            ):
                error += f"{line}\n"
            error += "Run test again with BLESS=ovewrite to bless the test."
            raise Exception(error)


def remove_lines(path: GenericPath, lines: List[int]):
    lines = set(lines)

    output = []
    with open(path) as f:
        for (index, line) in enumerate(f):
            if index in lines:
                continue
            output.append(line)

    with open(path, "w") as f:
        for line in output:
            f.write(line)
