import contextlib
import os
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


@contextlib.contextmanager
def change_workdir(workdir: GenericPath):
    cwd = os.getcwd()
    try:
        os.chdir(workdir)
        yield
    finally:
        os.chdir(cwd)


# Fixture
@pytest.fixture(scope="function")
def gmx() -> GMX:
    gmx_path = os.environ.get("GMX_PATH")
    return GMX(gmx_path)
