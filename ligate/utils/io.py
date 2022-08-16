import logging
import os
import shutil
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

from .paths import GenericPath, normalize_path


# Deletion
def delete_file(path: GenericPath):
    """
    Deletes a file at `path`.
    """
    logging.debug(f"Removing {path}")
    os.unlink(path)


def delete_path(path: GenericPath):
    """
    Delete a file or directory at `path`, ignoring errors.
    """
    logging.debug(f"Removing {path}")
    shutil.rmtree(path, ignore_errors=True)


def delete_files(paths: List[GenericPath]):
    for path in paths:
        delete_file(path)


# Copying
def copy_files(files: List[GenericPath], target_dir: GenericPath):
    """
    Copies the provided `files` to the `target_dir`.
    """
    target_dir = ensure_directory(target_dir)

    for path in files:
        shutil.copy(path, target_dir)


def move_file(src: GenericPath, dst: GenericPath):
    dst = Path(dst)
    if dst.is_dir():
        dst = dst / Path(src).name
    logging.debug(f"Moving file {src} to {dst}")
    shutil.move(src, dst)


def move_files(files: Iterable[GenericPath], dst: GenericPath):
    for file in files:
        move_file(file, dst)


def copy_directory(src: GenericPath, dst: GenericPath):
    logging.debug(f"Copying directory {src} to {dst}")
    shutil.copytree(
        src,
        dst,
        dirs_exist_ok=True,
    )


# File content manipulation and reading
def iterate_file_lines(file: Path, skip=0) -> Iterable[str]:
    """
    Lazily iterates the lines of the given `file`.
    """
    with open(file) as f:
        for (index, line) in enumerate(f):
            line = line.strip()
            if index >= skip:
                yield line


def append_lines_to(lines: Iterable[str], target: Path, until: Optional[str] = None):
    """
    Reads lines from `lines` and appends them to `target`.
    When a line in `file` equals `until`, the appending will end.
    """
    with open(target, "a") as target:
        for line in lines:
            if until is not None and line == until:
                break
            target.write(f"{line}\n")


def append_to(file: Path, text: str):
    """
    Appends `text` to the provided `file`.
    """
    with open(file, "a") as file:
        file.write(text)


def replace_in_place(path: GenericPath, replacements: List[Tuple[str, str]]):
    """
    Replaces multiple occurences (`before`, `after`) in `path`.
    """
    with open(path) as f:
        data = f.read()
    for (src, target) in replacements:
        data = data.replace(src, target)

    with open(path, "w") as f:
        f.write(data)


# File iteration
def iterate_files(
    directory: GenericPath, filter: Optional[Callable[[Path], bool]] = None
) -> Iterable[Path]:
    """
    Iterates files in the given directory (non-recursively).
    Optionally, you can select a filter for each file.
    """
    directory = Path(directory)
    for file in os.listdir(directory):
        full_path = directory / file
        if full_path.is_file():
            if filter is None or filter(full_path):
                yield full_path


def iterate_directories(path: GenericPath) -> List[Path]:
    """
    Iterates through directories (non-recursively) in the given `path`.
    The directories are sorted by their filepath.
    """
    path = Path(path)
    dirs = [
        path.absolute() / child for child in os.listdir(path) if (path / child).is_dir()
    ]
    return sorted(dirs)


# Querying
def check_dir_exists(path: GenericPath):
    path = Path(path)
    if not path.is_dir():
        error = f"The path {path} is not an existing directory."
        if path.is_file():
            error += " It is a file."
        elif not path.exists():
            error += " It does not exist."
        raise Exception(error)


def file_has_extension(path: GenericPath, extension: str) -> bool:
    return Path(path).suffix.strip(".") == extension


def check_has_extension(path: GenericPath, extension: str):
    actual_extension = Path(path).suffix.strip(".")
    if actual_extension != extension:
        raise Exception(
            f"Path {path} should have extension {extension}, but it has {actual_extension}"
        )


# General utility
def remap_paths_to_dir(paths: List[GenericPath], dir: Path) -> List[Path]:
    """
    Maps the given `paths` so that they are relative to the given `dir`.
    """
    return [dir / path for path in paths]


def ensure_directory(path: GenericPath, clear=False) -> Path:
    """
    Makes sure that the directory at `path` exists and returns an absolute path to it.
    If `clear` is True, the contents of the directory will be removed.
    """
    if os.path.isfile(path) and not os.path.isdir(path):
        path = os.path.dirname(path)
    if clear and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    logging.debug(f"Creating directory {path}")
    os.makedirs(path, exist_ok=True)
    return normalize_path(path)
