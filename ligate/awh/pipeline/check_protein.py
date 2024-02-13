from pathlib import Path

from ..input import AWHInput
from ..pdb import check_protein_fasta, detect_gaps, pdb2fasta
from ...utils.paths import active_workdir
from ...utils.tracing import trace, trace_fn


@trace_fn()
def check_protein(input: AWHInput, workdir: Path):
    fasta = Path("protein.fasta")
    pdb_file = input.input_dir / "protein_amber" / "protein.pdb"

    with active_workdir(workdir):
        with trace("pdb2fasta"):
            pdb2fasta(pdb_file, fasta)
        with trace("check_protein"):
            check_protein_fasta(fasta)
        with trace("detect_gaps"):
            detect_gaps(pdb_file)
