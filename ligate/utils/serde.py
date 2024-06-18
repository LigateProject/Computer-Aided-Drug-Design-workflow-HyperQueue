from pathlib import Path
from typing import Type, TypeVar

import serde.yaml

T = TypeVar("T")


def deserialize_yaml(cls: Type[T], path: Path) -> T:
    with open(path) as f:
        return serde.yaml.from_yaml(cls, f.read())
