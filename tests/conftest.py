import os
import sys
from pathlib import Path

import pytest

PYTEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PYTEST_DIR)

sys.path.insert(0, ROOT_DIR)


from ligate.gmx import GMX  # noqa
from ligate.utils.io import GenericPath  # noqa


def data_path(path: GenericPath) -> Path:
    return (Path(PYTEST_DIR) / "data" / path).absolute()


# Fixture
@pytest.fixture(scope="function")
def gmx() -> GMX:
    return GMX()
