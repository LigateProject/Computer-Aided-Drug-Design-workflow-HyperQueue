from ligate.awh.pdb2fasta import pdb2fasta

from .utils.io import read_file


def test_convert_pdb_to_fasta(data_dir, tmp_path, snapshot):
    pdb_path = data_dir / "ligen/p38/protein_amber/protein.pdb"
    output = tmp_path / "out.fasta"
    pdb2fasta(pdb_path, output)
    assert snapshot() == read_file(output)
