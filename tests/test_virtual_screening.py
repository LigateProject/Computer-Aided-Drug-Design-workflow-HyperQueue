import os
from pathlib import Path
from typing import List

import pytest

from ligate.awh.pipeline.virtual_screening.ligen.common import LigenTaskContext
from ligate.awh.pipeline.virtual_screening.ligen.expansion import (
    ExpansionConfig,
    ligen_expand_smi,
)
from tests.conftest import get_test_data
from tests.utils.io import check_files_are_equal


def test_expand_single_molecule(ligen_ctx: LigenTaskContext, tmp_path: Path):
    output_path = expand(
        ligen_ctx, get_test_data("ligen/smi/a/input.smi"), tmp_path / "out.smi"
    )
    check_files_are_equal(get_test_data("ligen/smi/a/output.smi"), output_path)


def test_expand_multiple_molecules(ligen_ctx: LigenTaskContext, tmp_path: Path):
    output_path = expand(
        ligen_ctx, get_test_data("ligen/smi/c/input.smi"), tmp_path / "out.smi"
    )
    check_files_are_equal(get_test_data("ligen/smi/c/output.smi"), output_path)


def test_expand_combined(ligen_ctx: LigenTaskContext, tmp_path):
    """
    Check that expanding two inputs, each with a single molecule is the same as expanding a single
    input with two molecules.
    """
    a = get_test_data("ligen/smi/a/input.smi")
    b = get_test_data("ligen/smi/b/input.smi")
    output_a = expand(ligen_ctx, a, tmp_path / "a.out")
    output_b = expand(ligen_ctx, b, tmp_path / "b.out")

    merged_input = tmp_path / "merged.smi"
    merge_files([a, b], merged_input)

    merged_output = expand(ligen_ctx, merged_input, tmp_path / "merged.out")

    ab_output = tmp_path / "ab.out"
    merge_files([output_a, output_b], ab_output)

    check_files_are_equal(merged_output, ab_output, bless=False)


def merge_files(files: List[Path], target: Path):
    with open(target, "w") as output:
        for file in files:
            with open(file) as f:
                for line in f:
                    print(line, end="", file=output)


def expand(ligen_ctx: LigenTaskContext, input: Path, output: Path) -> Path:
    ligen_expand_smi(
        ligen_ctx,
        ExpansionConfig(
            id="foo",
            input_smi=input,
            output_smi=output,
        ),
    )
    return output


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
