import dataclasses


@dataclasses.dataclass
class MinimizationParams:
    steps: int
    cores: int
