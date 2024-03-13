import os
from pathlib import Path

import pytest

from ligate.awh.pipeline.virtual_screening.ligen.common import LigenTaskContext


# Fixtures
@pytest.fixture(scope="session")
def ligen_container() -> Path:
    path = os.environ.get("LIGEN_CONTAINER")
    if path is None:
        raise Exception(
            "Environment variable `LIGEN_CONTAINER` not set. Point it to a SIF apptainer image containing Ligen."
        )
    container = Path(path).absolute()
    assert container.is_file()
    return container


@pytest.fixture(scope="session")
def ligen_ctx(ligen_container) -> LigenTaskContext:
    return LigenTaskContext(workdir=Path(os.getcwd()), container_path=ligen_container)
