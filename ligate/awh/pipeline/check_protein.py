from pathlib import Path

from ..input import AWHInput
from ..pdb import check_protein_fasta, detect_gaps, pdb2fasta
from ..structureNormalisation import normalise_structure
from ...utils.io import copy_files
from ...utils.paths import active_workdir
from ...utils.tracing import trace, trace_fn


@trace_fn()
def check_protein(input: AWHInput, workdir: Path):
    fasta = Path("protein.fasta")
    pdb_file = input.input_dir / "protein_amber" / "protein.pdb"

    with active_workdir(workdir):
        copy_files([pdb_file], ".")
        input_protein = Path("protein.pdb")

        with trace("pdb2fasta"):
            pdb2fasta(input_protein, fasta)
        with trace("check protein"):
            check_protein_fasta(fasta)
        with trace("detect gaps"):
            detect_gaps(input_protein)

        normalized_pdb = Path("protein_normalized.pdb")
        with trace("normalize structure"):
            normalise_structure(input_protein, fasta, normalized_pdb)
