import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .paths import GenericPath


def execute_command(
    args: List[Union[str, Path, int]],
    *,
    input: Optional[bytes] = None,
    workdir: Optional[GenericPath] = None,
    env: Optional[Dict[str, str]] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    env = env or {}
    environment = replace_env(**env)

    cmd = normalize_arguments(args)
    kwargs = {}
    if input is not None:
        kwargs["input"] = input
    else:
        kwargs["stdin"] = subprocess.DEVNULL

    env = " ".join([f"{k}={v}" for (k, v) in sorted(env.items(), key=lambda v: v[0])])
    logging.debug(f"Executing {env} `{' '.join(cmd)}` at `{workdir or os.getcwd()}`")
    result = subprocess.run(cmd, cwd=workdir, env=environment, **kwargs)
    if check and result.returncode != 0:
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


def replace_env(**kwargs) -> Dict[str, str]:
    env = os.environ.copy()
    env.update(kwargs)
    return env
