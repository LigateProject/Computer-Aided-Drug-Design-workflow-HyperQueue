import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils.paths import GenericPath, resolve_path


class GMX:
    def __init__(self, path: Optional[Path] = None):
        self.gmx_path = (path or Path("gmx")).resolve()

    @property
    def binary_path(self) -> Path:
        return self.gmx_path

    def editconf(self, input: GenericPath, output: GenericPath):
        input = resolve_path(input)
        output = resolve_path(output)

        return self.execute(
            [
                "editconf",
                "-f",
                str(input),
                "-o",
                str(output),
                "-bt",
                "dodecahedron",
                "-d",
                "1.5",
            ]
        )

    def execute(
        self,
        args: List[str],
        *,
        input: Optional[bytes] = None,
        workdir: Optional[GenericPath] = None,
        env: Optional[Dict[str, str]] = None,
    ):
        environment = os.environ.copy()
        if env is not None:
            environment.update(env)

        cmd = normalize_arguments([self.gmx_path, *args])
        kwargs = {}
        if input is not None:
            kwargs["input"] = input
        else:
            kwargs["stdin"] = subprocess.DEVNULL

        logging.info(f"Executing `{' '.join(cmd)}` in {workdir or os.getcwd()}")
        result = subprocess.run(cmd, cwd=workdir, env=environment, **kwargs)
        if result.returncode != 0:
            raise Exception(
                f"`{' '.join(cmd)}` resulted in error. Exit code: {result.returncode}"
            )
        return result


def normalize_arguments(input: List[Any]) -> List[str]:
    output = []
    allowed_types = (str, Path, int)

    for item in input:
        if any(isinstance(item, t) for t in allowed_types):
            output.append(str(item))
        else:
            raise Exception(
                f"Invalid type `{type(item)}` with value `{item}` passed as an executable argument"
            )
    return output
