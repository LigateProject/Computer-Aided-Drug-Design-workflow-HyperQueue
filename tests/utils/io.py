import difflib

from ligate.utils.io import GenericPath


def check_file_equals(path: str, content):
    with open(path) as f:
        assert f.read() == str(content)


def check_file_equality(expected: GenericPath, actual: GenericPath):
    with open(expected) as expected_file:
        with open(actual) as actual_file:
            expected_file = expected_file.read()
            actual_file = actual_file.read()

            if expected_file != actual_file:
                error = f"{expected} and {actual} do not match\n"
                for line in difflib.unified_diff(expected_file.splitlines(),
                                                 actual_file.splitlines(),
                                                 fromfile=str(expected),
                                                 tofile=str(actual)):
                    error += f"{line}\n"
                raise Exception(error)
