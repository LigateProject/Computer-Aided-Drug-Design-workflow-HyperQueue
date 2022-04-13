import dataclasses
from pathlib import Path


@dataclasses.dataclass
class Context:
    pmx_dir: Path
    root_dir: Path
    mdp_dir: Path
    gmx_binary: Path

    def __post_init__(self):
        self.root_dir.mkdir(parents=True, exist_ok=True)
