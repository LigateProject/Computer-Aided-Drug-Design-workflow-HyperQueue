import contextlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

PYTEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PYTEST_DIR)

sys.path.insert(0, ROOT_DIR)


from ligate.gmx import GMX  # noqa
from ligate.utils.io import GenericPath  # noqa


# Utility functions
def data_path(path: GenericPath) -> Path:
    return (Path(PYTEST_DIR) / "data" / path).absolute()


def is_bless_enabled() -> bool:
    return os.environ.get("BLESS") is not None


@contextlib.contextmanager
def change_workdir(workdir: GenericPath):
    cwd = os.getcwd()
    try:
        os.chdir(workdir)
        yield
    finally:
        os.chdir(cwd)


def gromacs_sanity_check(path: GenericPath):
    try:
        subprocess.run([path], check=True)
    except BaseException as e:
        raise Exception(
            f"It was not possible to execute Gromacs\n{e}\nIf Gromacs is not "
            f"available globally, provide a path to it in environment variable "
            f"`GMX_PATH`."
        )


# Fixture
@pytest.fixture(scope="function")
def gmx() -> GMX:
    gmx_path = os.environ.get("GMX_PATH")
    gmx = GMX(gmx_path)
    gromacs_sanity_check(str(gmx.binary_path))
    return gmx
