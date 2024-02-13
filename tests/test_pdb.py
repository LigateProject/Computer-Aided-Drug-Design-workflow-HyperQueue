from ligate.awh.pdb import check_protein_fasta, detect_gaps, pdb2fasta

from .utils.io import read_file


def test_convert_pdb_to_fasta(data_dir, tmp_path, snapshot):
    pdb_path = data_dir / "ligen/p38/protein_amber/protein.pdb"
    output = tmp_path / "out.fasta"
    pdb2fasta(pdb_path, output)
    assert snapshot() == read_file(output)


def test_check_protein_fasta(data_dir, tmp_path):
    pdb_path = data_dir / "ligen/p38/protein_amber/protein.fasta"
    check_protein_fasta(pdb_path)


def test_detect_gaps(data_dir, tmp_path):
    pdb_path = data_dir / "ligen/p38/protein_amber/protein.pdb"
    detect_gaps(pdb_path)
