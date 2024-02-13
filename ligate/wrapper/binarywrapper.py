import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
        return execute_command([self.binary_path, *args], input=input, workdir=workdir, env=env)


def execute_command(
    args: List[Union[str, Path, int]],
    *,
    input: Optional[bytes] = None,
    workdir: Optional[GenericPath] = None,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    environment = os.environ.copy()
    if env is not None:
        environment.update(env)

    cmd = normalize_arguments(args)
    kwargs = {}
    if input is not None:
        kwargs["input"] = input
    else:
        kwargs["stdin"] = subprocess.DEVNULL

    logging.debug(f"Executing `{' '.join(cmd)}` in {workdir or os.getcwd()}")
    result = subprocess.run(cmd, cwd=workdir, env=environment, **kwargs)
    if result.returncode != 0:
        raise Exception(f"`{' '.join(cmd)}` resulted in error. Exit code: {result.returncode}")
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
