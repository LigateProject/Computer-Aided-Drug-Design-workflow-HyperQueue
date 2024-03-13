from pathlib import Path
from typing import Dict, List, Optional, Union

from ..utils.cmd import execute_command
from ..utils.paths import GenericPath


class BinaryWrapper:
    def __init__(self, path: Optional[GenericPath], fallback: str):
        self.binary_path = Path(path).resolve() if path is not None else Path(fallback)

    def execute(
        self,
        args: List[Union[str, Path, int]],
        *,
        input: Optional[bytes] = None,
        workdir: Optional[GenericPath] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        return execute_command(
            [self.binary_path, *args], input=input, workdir=workdir, env=env
        )
