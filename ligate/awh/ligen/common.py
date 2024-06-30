from dataclasses import dataclass
from pathlib import Path


@dataclass
class LigenTaskContext:
    workdir: Path
    container_path: Path
