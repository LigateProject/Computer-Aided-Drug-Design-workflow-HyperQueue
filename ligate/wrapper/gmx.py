from typing import Optional

from ..utils.paths import GenericPath
from .binarywrapper import BinaryWrapper


class GMX(BinaryWrapper):
    def __init__(self, path: Optional[GenericPath] = None):
        super().__init__(path, fallback="gmx")
