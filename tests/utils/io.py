import difflib
import shutil

from ligate.utils.io import GenericPath

from ..conftest import is_bless_enabled


def check_file_equals(path: str, content):
    with open(path) as f:
        assert f.read() == str(content)


def check_files_are_equal(expected: GenericPath, actual: GenericPath):
    try:
        expected_file = open(expected)
    except FileNotFoundError:
        if is_bless_enabled():
            shutil.copyfile(actual, expected)
            return

        raise Exception(
            "Expected file `expected` not found. Run test again with BLESS=1 to "
            "create it."
        )

    with open(actual) as actual_file:
        expected_file = expected_file.read()
        actual_file = actual_file.read()

        if expected_file != actual_file:
            error = f"{expected} and {actual} do not match\n"
            for line in difflib.unified_diff(
                expected_file.splitlines(),
                actual_file.splitlines(),
                fromfile=str(expected),
                tofile=str(actual),
            ):
                error += f"{line}\n"
            raise Exception(error)
