import os
from typing import Tuple, List


def replace_in_place(path: str, replacements: List[Tuple[str, str]]):
    with open(path) as f:
        data = f.read()
    for (src, target) in replacements:
        data = data.replace(src, target)

    with open(path, "w") as f:
        f.write(data)


def remove(path: str):
    os.unlink(path)
