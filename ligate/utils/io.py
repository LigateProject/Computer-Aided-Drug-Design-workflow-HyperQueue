import os
import shutil
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union


GenericPath = Union[Path, str]


def replace_in_place(path: GenericPath, replacements: List[Tuple[str, str]]):
    with open(path) as f:
        data = f.read()
    for (src, target) in replacements:
        data = data.replace(src, target)

    with open(path, "w") as f:
        f.write(data)


def delete_file(path: GenericPath):
    os.unlink(path)


def ensure_directory(path: GenericPath, clear=False) -> Path:
    if os.path.isfile(path) and not os.path.isdir(path):
        path = os.path.dirname(path)
    if clear and os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
    return Path(path).absolute()


def copy_files(paths: List[GenericPath], target_dir: GenericPath):
    target_dir = ensure_directory(target_dir)

    for path in paths:
        shutil.copy(path, target_dir)


def paths_in_dir(paths: List[GenericPath], dir: Path) -> List[Path]:
    return [dir / path for path in paths]


def append_lines_to(lines: Iterable[str], target: Path, until: Optional[str] = None):
    """Reads lines from `lines` and appends them to `target`.
    When a line in `file` equals `until`, the appending will end."""
    with open(target, "a") as target:
        for line in lines:
            if until is not None and line == until:
                break
            target.write(f"{line}\n")


def append_to(target: Path, text: str):
    with open(target, "a") as target:
        target.write(text)


def get_file_lines(file: Path, skip=0) -> Iterable[str]:
    with open(file) as f:
        for (index, line) in enumerate(f):
            line = line.strip()
            if index >= skip:
                yield line
