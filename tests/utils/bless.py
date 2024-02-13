import enum
import os
import shutil
import subprocess
from pathlib import Path

from ligate.utils.paths import GenericPath


class BlessMode(enum.Enum):
    """
    Test files will not be blessed
    """

    NoBless = enum.auto()
    """
    Test files will be created if they do not exist
    """
    Create = enum.auto()
    """
    Test files will be created if they do not exist or overwritten
    if they exist
    """
    Overwrite = enum.auto()

    def can_create(self) -> bool:
        return self == BlessMode.Create or self == BlessMode.Overwrite


def get_bless_mode() -> BlessMode:
    bless_mode = os.environ.get("BLESS")
    if bless_mode is None:
        return BlessMode.NoBless
    elif bless_mode == "create":
        return BlessMode.Create
    elif bless_mode == "overwrite":
        return BlessMode.Overwrite
    else:
        raise Exception(
            f"Invalid bless mode {bless_mode}. Use `create` or `overwrite`."
        )


def bless_file(expected: GenericPath, actual: GenericPath, mode: BlessMode):
    os.makedirs(Path(expected).parent, exist_ok=True)
    shutil.copyfile(actual, expected)

    if mode == BlessMode.Overwrite:
        print(f"Bless: overwriting file {expected} with contents of {actual}")
    elif mode == BlessMode.Create:
        print(f"Bless: creating file {expected} with contents of {actual}")
    try:
        subprocess.run(["git", "add", str(expected)])
    except:
        pass
