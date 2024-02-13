from pathlib import Path

from ..utils.error import AWHError


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
            if (
                line[17:20] not in aminoAcids
                and line[17:20] != "ACE"
                and line[17:20] != "NME"
            ):
                raise AWHError(
                    f"Non-standard residue ({line[17:20]}) found in protein coordinates!"
                )
            if (
                line[22:27] != previousResidue
                and line[17:20] != "ACE"
                and line[17:20] != "NME"
            ):
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
