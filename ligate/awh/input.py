import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class AWHInput:
    protein_pdb: Path

    def __post_init__(self):
        assert self.protein_pdb.is_file()
        assert self.protein_pdb.suffix == ".pdb"
