import dataclasses
from pathlib import Path

from .wrapper.gromacs import Gromacs


@dataclasses.dataclass
class Context:
    workdir: Path
    mdpdir: Path
    gmx: Gromacs

    def __post_init__(self):
        self.workdir = self.workdir.resolve()
        self.mdpdir = self.mdpdir.resolve()
        self.workdir.mkdir(parents=True, exist_ok=True)
