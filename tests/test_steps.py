from pathlib import Path

import pytest

from ligate.awh.pipeline.check_protein import check_protein
from .utils.io import read_file


def test_check_protein(protein_bace_amber, tmp_path, snapshot):
    check_protein(protein_bace_amber, tmp_path)
    assert snapshot() == read_file(tmp_path / "protein_normalized.pdb")


@pytest.fixture
def protein_bace_amber(data_dir) -> Path:
    return data_dir / "ligen/bace/protein_amber/protein.pdb"
