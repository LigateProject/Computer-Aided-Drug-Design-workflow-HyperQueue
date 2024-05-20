import contextlib
import difflib
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

from ligate.utils.io import ensure_directory
from ligate.utils.paths import GenericPath

from .bless import BlessMode, bless_file, get_bless_mode


def check_files_are_equal(expected: GenericPath, actual: GenericPath, bless=True):
    bless_mode = get_bless_mode() if bless else BlessMode.NoBless

    try:
        expected_file = open(expected, "rb")
    except FileNotFoundError:
        if bless_mode.can_create():
            bless_file(expected, actual, bless_mode)
            return

        raise Exception(
            f"Expected file `{expected}` not found. Run test again with BLESS=create to "
            "create it."
        )

    with open(actual, "rb") as actual_file:
        expected_file = expected_file.read()
        actual_file = actual_file.read()

        if expected_file != actual_file:
            if bless_mode == BlessMode.Overwrite:
                bless_file(expected, actual, bless_mode)
                return

            error = f"{expected} and {actual} do not match\n"
            for line in difflib.unified_diff(
                expected_file.decode().splitlines(),
                actual_file.decode().splitlines(),
                fromfile=str(expected),
                tofile=str(actual),
            ):
                error += f"{line}\n"
            if bless:
                error += "Run test again with BLESS=overwrite to bless the test."
            raise Exception(error)


def check_dirs_are_equal(expected: GenericPath, actual: GenericPath, bless=True):
    expected = Path(expected).absolute()
    actual = Path(actual).absolute()

    assert actual.is_dir()
    if not expected.exists() and bless and get_bless_mode().can_create():
        ensure_directory(expected)

    assert expected.is_dir()

    found_paths = set()
    for name in sorted(os.listdir(actual)):
        path = actual / name
        if path.is_file():
            check_files_are_equal(expected / name, path, bless=bless)
        elif path.is_dir():
            check_dirs_are_equal(expected / name, path, bless=bless)
        else:
            raise Exception(f"Unknown path entry at {path}")
        found_paths.add(name)

    missing_paths = []
    for name in sorted(os.listdir(expected)):
        if name not in found_paths:
            missing_paths.append(name)
    if missing_paths:
        raise Exception(
            f"Expected to find {sorted(missing_paths)} in {actual}, because they are in {expected}"
        )


def remove_lines(path: GenericPath, lines: List[int]):
    lines = set(lines)

    output = []
    with open(path) as f:
        for index, line in enumerate(f):
            if index in lines:
                continue
            output.append(line)

    with open(path, "w") as f:
        for line in output:
            f.write(line)


def read_file(path: GenericPath) -> str:
    with open(path) as f:
        return f.read()


@contextlib.contextmanager
def check_immutable_dir(path: Path):
    """
    Context manager that checks that `path` has not been modified after the manager exits.
    """
    assert path.is_dir()

    with tempfile.TemporaryDirectory() as dir:
        original_copy = Path(dir) / "original"
        shutil.copytree(path, original_copy)
        try:
            yield
        finally:
            check_dirs_are_equal(original_copy, path, bless=False)
