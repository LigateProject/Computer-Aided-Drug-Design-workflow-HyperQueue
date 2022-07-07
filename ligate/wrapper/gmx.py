from typing import Optional

from ..utils.paths import GenericPath, resolve_path
from .binarywrapper import BinaryWrapper


class GMX(BinaryWrapper):
    def __init__(self, path: Optional[GenericPath] = None):
        super().__init__(path, fallback="gmx")

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
