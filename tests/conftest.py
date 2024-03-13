import os
import subprocess
import sys
from pathlib import Path

import pytest

PYTEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PYTEST_DIR)

sys.path.insert(0, ROOT_DIR)

from ligate.utils.paths import GenericPath  # noqa
from ligate.wrapper.babel import Babel  # noqa
from ligate.wrapper.binarywrapper import BinaryWrapper  # noqa
from ligate.wrapper.gmx import GMX  # noqa
from ligate.wrapper.stage import Stage  # noqa


def get_test_data(path: str) -> Path:
    return (Path(PYTEST_DIR) / "data").absolute() / path


# Pytest configuration
def pytest_collection_modifyitems(config, items):
    """
    Skip tests that are marked with `skipmarks`, but for which `-m <skipmark>` was not passed.
    """
    skipmarks = ("slow",)
    markexpr = config.option.markexpr
    for skipmark in skipmarks:
        if skipmark == markexpr:
            continue
        skipper = pytest.mark.skip(reason=f"Only run when -m {skipmark} is given")
        for item in items:
            if skipmark in item.keywords:
                item.add_marker(skipper)


# Fixtures
@pytest.fixture(scope="session")
def data_dir() -> Path:
    return (Path(PYTEST_DIR) / "data").absolute()


@pytest.fixture(scope="function")
def gmx() -> GMX:
    gmx_path = os.environ.get("GMX_PATH")
    gmx = GMX(gmx_path)
    wrapper_sanity_check(gmx, "Gromacs", "GMX_PATH")
    return gmx


@pytest.fixture(scope="function")
def babel() -> Babel:
    babel_path = os.environ.get("OPENBABEL_PATH")
    babel = Babel(babel_path)
    wrapper_sanity_check(babel, "OpenBabel", "OPENBABEL_PATH")
    return babel


@pytest.fixture(scope="function")
def stage() -> Stage:
    return Stage()


def wrapper_sanity_check(wrapper: BinaryWrapper, name: str, env_var: str):
    try:
        subprocess.run(
            [str(wrapper.binary_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except BaseException as e:
        raise Exception(
            f"It was not possible to execute {name}\n{e}\nIf {name} is not "
            f"available globally, provide a path to it in environment variable "
            f"`{env_var}`."
        )
