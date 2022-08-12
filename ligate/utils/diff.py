from pathlib import Path

from .io import GenericPath


def check_diff(path: GenericPath, workdir: GenericPath, workdir_ref: GenericPath):
    """
    Checks the diff between the file `path` in `workdir` and `workdir_ref`.
    """
    import difflib

    rel_path = Path(path).relative_to(workdir)
    original_path = Path(workdir_ref) / rel_path

    with open(path) as f:
        content = [line.strip() for line in f.read().strip().splitlines()]
    with open(original_path) as f:
        content_orig = [line.strip() for line in f.read().strip().splitlines()]

    diff = ""
    for line in difflib.unified_diff(
        content,
        content_orig,
        fromfile=str(path),
        tofile=str(original_path),
        lineterm="",
    ):
        diff += f"{line}\n"
    if diff:
        raise Exception(diff)
