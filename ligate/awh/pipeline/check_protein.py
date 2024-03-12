from pathlib import Path

from ..pdb import check_protein_fasta, detect_gaps, pdb2fasta
from ..structureNormalisation import normalise_structure
from ...utils.io import copy_files
from ...utils.paths import active_workdir
from ...utils.tracing import trace, trace_fn


@trace_fn()
def check_protein(protein: Path, workdir: Path):
    fasta = Path("protein.fasta")

    assert protein.suffix == ".pdb"

    with active_workdir(workdir):
        copy_files([protein], ".")
        input_protein = workdir / protein.name

        with trace("pdb2fasta"):
            pdb2fasta(input_protein, fasta)
        with trace("check protein"):
            check_protein_fasta(fasta)
        with trace("detect gaps"):
            detect_gaps(input_protein)

        normalized_pdb = Path("protein_normalized.pdb")
        with trace("normalize structure"):
            normalise_structure(input_protein, fasta, normalized_pdb)
