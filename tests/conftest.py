import contextlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

PYTEST_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PYTEST_DIR)

sys.path.insert(0, ROOT_DIR)


from ligate.utils.io import GenericPath  # noqa
from ligate.wrapper.babel import Babel  # noqa
from ligate.wrapper.binarywrapper import BinaryWrapper  # noqa
from ligate.wrapper.gmx import GMX  # noqa


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


def wrapper_sanity_check(wrapper: BinaryWrapper, name: str, env_var: str):
    try:
        subprocess.run([str(wrapper.binary_path)], check=True)
    except BaseException as e:
        raise Exception(
            f"It was not possible to execute {name}\n{e}\nIf {name} is not "
            f"available globally, provide a path to it in environment variable "
            f"`{env_var}`."
        )


# Fixtures
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
