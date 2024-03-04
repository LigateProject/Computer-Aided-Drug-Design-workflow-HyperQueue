import dataclasses
from pathlib import Path


@dataclasses.dataclass(frozen=True)
class AWHInput:
    input_dir: Path
