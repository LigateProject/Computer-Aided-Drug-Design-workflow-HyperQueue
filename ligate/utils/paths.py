import contextlib
import logging
import os
from pathlib import Path
from typing import Union

GenericPath = Union[Path, str]

PATH_STACK = []


@contextlib.contextmanager
def active_workdir(path: GenericPath):
    path = Path(path)
    if not path.is_absolute():
        root = get_active_dir()
        path = root.joinpath(path)
    PATH_STACK.append(path)

    cwd = os.getcwd()
    path.mkdir(parents=True, exist_ok=True)
    os.chdir(path)

    try:
        logging.debug(f"Switching directory to {path}")
        yield path
    finally:
        os.chdir(cwd)
        logging.debug(f"Switching directory back to {cwd}")
        PATH_STACK.pop()


def get_active_dir() -> Path:
    return Path(PATH_STACK[-1] if PATH_STACK else os.getcwd()).absolute()


def resolve_path(path: GenericPath, create_parent=True) -> Path:
    from .io import ensure_directory

    path = Path(path)
    if path.is_absolute():
        return path
    path = get_active_dir().joinpath(path)
    if create_parent:
        ensure_directory(path)
    return path


def normalize_path(path: GenericPath) -> Path:
    """
    Makes the path absolute and resolves any links in it.
    """
    return Path(path).resolve()
