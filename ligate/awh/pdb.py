import tempfile
import typing
from pathlib import Path

from ..utils.cmd import execute_command
from ..utils.error import AWHError
from ..utils.io import delete_file, iterate_file_lines


def pdb2fasta(input_pdb: Path, output_fasta: Path):
    """
    Convert a PDB file to a FASTA file.
    """
    # dictionary for one-letter code
    aminoAcids = dict(
        {
            "ARG": "R",
            "HIS": "H",
            "LYS": "K",
            "ASP": "D",
            "GLU": "E",
            "ASN": "N",
            "GLN": "Q",
            "SER": "S",
            "THR": "T",
            "CYS": "C",
            "GLY": "G",
            "PRO": "P",
            "ALA": "A",
            "ILE": "I",
            "LEU": "L",
            "MET": "M",
            "PHE": "F",
            "TYR": "Y",
            "TRP": "W",
            "VAL": "V",
            "HID": "H",
            "HIE": "H",
            "HIP": "H",
            "LYN": "K",
            "CYM": "C",
            "CYX": "C",
            "ASH": "D",
            "GLH": "E",
        }
    )

    with open(input_pdb) as f:
        lines = f.readlines()

    # convert PDB to FASTA files
    sequence = dict()
    previousResidue = "000"
    countTER = 0
    for line in lines:
        # no input PDB file contains the keyword "HETATM" in this data set
        # TODO: how to handle water molecules and ions in CADD workflow
        if "ATOM" in line:
            if line[21] not in sequence:
                sequence.update({line[21]: ""})
            if line[17:20] not in aminoAcids and line[17:20] != "ACE" and line[17:20] != "NME":
                raise AWHError(
                    f"Non-standard residue ({line[17:20]}) found in protein coordinates!"
                )
            if line[22:27] != previousResidue and line[17:20] != "ACE" and line[17:20] != "NME":
                sequence[line[21]] += aminoAcids[line[17:20]]
                previousResidue = line[22:27]
        if "TER" in line:
            countTER += 1

    with open(output_fasta, "w") as f:
        for chain in sequence:
            f.write("%s\n" % (">" + chain))
            [
                f.write("%s\n" % sequence[chain][j : j + 60])
                for j in range(0, len(sequence[chain]), 60)
            ]


def check_protein_fasta(input_fasta: Path):
    ## We only want to remove a protein from the data set if the ligand-binding core is a membrane protein
    ## We don't want to remove it due to membrane anchors etc. irrelevant to the protein-ligand interaction
    ## Therefore, we use our self-made FASTA file for this check
    # Check whether it is a membrane protein
    # tmbed predict -f protein.fasta -p protein.pred --out-format 0 --no-use-gpu
    file = tempfile.NamedTemporaryFile(delete=False)
    execute_command(
        [
            "tmbed",
            "predict",
            "-f",
            input_fasta,
            "-p",
            file.name,
            "--out-format",
            "0",
            "--no-use-gpu",
        ]
    )
    lines = list(iterate_file_lines(file.name))
    last_line = lines[-1].strip()
    errors = "BbHhS"
    for c in errors:
        if c in last_line:
            output = "\n".join(lines)
            raise AWHError(
                f"Some residues of the target protein should be located in a membrane.\n\n{output}"
            )
    delete_file(file.name)


def detect_gaps(input_pdb: Path):
    from pdbtools.pdb_delhetatm import remove_hetatm

    with open(input_pdb) as f:
        lines = remove_hetatm(f)
        gap_count = pdbtools_pdb_gap_count_gaps(lines)
        if gap_count != 0:
            raise AWHError(
                "Input protein structure has gaps, but no canonical FASTA file was provided."
            )


def pdbtools_pdb_gap_count_gaps(lines: typing.Iterable[str]) -> int:
    """
    Detect gaps between residues in the opened PDB file.

    Inlined from the pdbtools pdb_gap script, because the original code writes to stdout.
    """

    centroid = " CA "  # respect spacing. 'CA  ' != ' CA '
    distance_threshold = 4.0 * 4.0

    def calculate_sq_atom_distance(i, j):
        """Squared euclidean distance between two 3d points"""
        return (
            (i[0] - j[0]) * (i[0] - j[0])
            + (i[1] - j[1]) * (i[1] - j[1])
            + (i[2] - j[2]) * (i[2] - j[2])
        )

    prev_at = (None, None, None, None, (None, None, None))
    model = 0
    n_gaps = 0
    for line in lines:
        if line.startswith("MODEL"):
            model = int(line[10:14])

        elif line.startswith("ATOM"):
            atom_name = line[12:16]
            if atom_name != centroid:
                continue

            resn = line[17:20]
            resi = int(line[22:26])
            chain = line[21]
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])

            at_uid = (model, chain, resi, resn, atom_name, (x, y, z))
            if prev_at[0] == at_uid[0] and prev_at[1] == at_uid[1]:
                d = calculate_sq_atom_distance(at_uid[5], prev_at[5])
                if d > distance_threshold:
                    n_gaps += 1
                elif prev_at[2] + 1 != at_uid[2]:
                    n_gaps += 1

            prev_at = at_uid

    return n_gaps
