from pathlib import Path

import pytest

from ligate.awh.pipeline.check_protein import check_protein


def test_check_protein(protein_bace_amber, tmp_path):
    check_protein(protein_bace_amber, tmp_path)


@pytest.fixture
def protein_bace_amber(data_dir) -> Path:
    return data_dir / "ligen/bace/protein_amber/protein.pdb"
