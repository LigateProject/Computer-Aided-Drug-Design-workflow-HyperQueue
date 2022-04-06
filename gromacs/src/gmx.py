import logging
import subprocess
from pathlib import Path
from typing import Optional, List

from .paths import GenericPath, resolve_path


class GMX:
    def __init__(self, path: Optional[Path] = None):
        self.gmx_path = path or Path("gmx")

    def editconf(self, input: GenericPath, output: GenericPath):
        input = resolve_path(input)
        output = resolve_path(output)

        return self.execute([
            "editconf",
            "-f", str(input),
            "-o", str(output),
            "-bt", "dodecahedron",
            "-d", "1.5"
        ])

    def execute(self, args: List[str], input: Optional[bytes] = None):
        cmd = [str(self.gmx_path), *args]
        kwargs = {}
        if input is not None:
            kwargs["input"] = input
        else:
            kwargs["stdin"] = subprocess.DEVNULL

        logging.debug(f"Executing {cmd}")
        result = subprocess.run(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                **kwargs)
        if result.returncode != 0:
            raise Exception(f"""
`{' '.join(cmd)}` resulted in error.
Exit code: {result.returncode}
Stdout: {result.stdout.decode()}
Stderr: {result.stderr.decode()}
""".strip())
        return result
