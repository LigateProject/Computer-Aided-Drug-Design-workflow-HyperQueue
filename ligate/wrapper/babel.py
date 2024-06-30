from typing import Optional

from ..utils.paths import GenericPath, resolve_path
from .binarywrapper import BinaryWrapper


class Babel(BinaryWrapper):
    def __init__(self, path: Optional[GenericPath] = None):
        super().__init__(path, fallback="babel")

    def normalize_mol2(self, input: GenericPath, output: GenericPath):
        input = resolve_path(input)
        output = resolve_path(output)

        return self.execute(["-i", "mol2", input, "-o", "mol2", output])
