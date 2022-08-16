import difflib
import os
import shutil
from pathlib import Path
from typing import List

from ligate.utils.paths import GenericPath

from ..conftest import BlessMode, get_bless_mode


def bless_file(expected: GenericPath, actual: GenericPath, mode: BlessMode):
    os.makedirs(Path(expected).parent, exist_ok=True)
    shutil.copyfile(actual, expected)

    if mode == BlessMode.Overwrite:
        print(f"Bless: overwriting file {expected} with contents of {actual}")
    elif mode == BlessMode.Create:
        print(f"Bless: creating file {expected} with contents of {actual}")


def check_files_are_equal(expected: GenericPath, actual: GenericPath):
    bless_mode = get_bless_mode()

    try:
        expected_file = open(expected)
    except FileNotFoundError:
        if bless_mode.can_create():
            bless_file(expected, actual, bless_mode)
            return

        raise Exception(
            "Expected file `expected` not found. Run test again with BLESS=create to "
            "create it."
        )

    with open(actual) as actual_file:
        expected_file = expected_file.read()
        actual_file = actual_file.read()

        if expected_file != actual_file:
            if bless_mode == BlessMode.Overwrite:
                bless_file(expected, actual, bless_mode)
                return

            error = f"{expected} and {actual} do not match\n"
            for line in difflib.unified_diff(
                expected_file.splitlines(),
                actual_file.splitlines(),
                fromfile=str(expected),
                tofile=str(actual),
            ):
                error += f"{line}\n"
            error += "Run test again with BLESS=overwrite to bless the test."
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
