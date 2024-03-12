import os
from pathlib import Path

import ost
from ost import conop, io, seq
from ost.mol.alg import Molck, MolckSettings
from promod3 import modelling

from ..utils.error import AWHError


def normalise_structure(input: Path, seqres_fasta: Path, output: Path):
    """
    Performs structure standardisation using the ProMod3 homology modelling toolbox.

    :param input: Structure file - supported " "formats: .pdb, .pdb.gz, .cif, .cif.gz
    :param seqres_fasta: SEQRES sequences in fasta format - expect one sequence per
    structure chain that should be normalized. Matching happens with sequence/chain names.
    Structure chains without matching sequence are dropped.
    :param output: Cleaned structure output in PDB format.
    """
    ent = load_structure(input)
    seqres = load_seqres(str(seqres_fasta))
    ent = clean(ent)
    ent = normalize(ent, seqres)
    io.SavePDB(ent, str(output))


def load_structure(structure_path: Path):
    """Read OST entity either from mmCIF or PDB."""
    structure_path = str(structure_path)

    if not os.path.exists(structure_path):
        raise AWHError(f"File not found: {structure_path}")

    # Determine file format from suffix.
    ext = structure_path.split(".")
    if ext[-1] == "gz":
        ext = ext[:-1]
    if len(ext) <= 1:
        raise AWHError(f"Could not determine format of file " f"{structure_path}.")
    sformat = ext[-1].lower()

    # increase loglevel, as we would pollute the info log with weird stuff
    ost.PushVerbosityLevel(ost.LogLevel.Error)
    # Load the structure
    if sformat in ["mmcif", "cif"]:
        entity = io.LoadMMCIF(structure_path)
        if len(entity.residues) == 0:
            raise AWHError(f"No residues found in file: {structure_path}")
    elif sformat in ["pdb"]:
        try:
            entity = io.LoadPDB(structure_path)
        except BaseException as e:
            raise AWHError(
                f"promod3 didn't work correctly (error reading input PDB file)."
            ) from e
        if len(entity.residues) == 0:
            raise AWHError(f"No residues found in file: {structure_path}")
    else:
        raise AWHError(
            f"Unknown/ unsupported file extension found for " f"file {structure_path}."
        )
    # restore old loglevel and return
    ost.PopVerbosityLevel()
    return entity


def load_seqres(seqres_path: str):
    """Read sequence list in fasta format"""
    if not os.path.exists(seqres_path):
        raise AWHError(f"file not found: {seqres_path}")
    seqres = io.LoadSequenceList(seqres_path, format="fasta")
    return seqres


def clean(ent):
    """Structure cleanup

    Performs the following processing:

    * to be documented
    """
    ms = MolckSettings(
        rm_unk_atoms=True,
        rm_non_std=True,
        rm_hyd_atoms=True,
        rm_oxt_atoms=True,
        rm_zero_occ_atoms=False,
        colored=False,
        map_nonstd_res=True,
        assign_elem=True,
    )
    Molck(ent, conop.GetDefaultLib(), ms)

    # requirement of running the processor here is considered a bug and is not
    # necessary starting from OpenStructure 2.4.0
    processor = conop.RuleBasedProcessor(conop.GetDefaultLib())
    processor.Process(ent)
    return ent.Select("peptide=true")


def normalize(ent, seqres):
    """GOGOGO"""

    # we really want to know that stuff...
    ost.PushVerbosityLevel(3)

    # make some noise on missing chains/sequences
    seqres_names = set([s.GetName() for s in seqres])
    chain_names = set([ch.GetName() for ch in ent.chains])
    for sn in seqres_names:
        if sn not in chain_names:
            ost.LogInfo(f"seqres with name {sn} without match in structure")
    for chn in chain_names:
        if chn not in seqres_names:
            ost.LogInfo(f"chain with name {chn} without match in seqres")

    aln_list = seq.AlignmentList()
    names = list()
    for s in seqres:
        name = s.GetName()
        if name in chain_names:
            chain_sel = ent.Select(f"cname={name}")
            try:
                aln = seq.alg.AlignToSEQRES(chain_sel, s, validate=False)
            except BaseException as e:
                raise AWHError(
                    f"Could not normalise structure due to alignment failure."
                ) from e
            aln.AttachView(1, chain_sel)
            aln_list.append(aln)
            names.append(name)

    mhandle = modelling.BuildRawModel(aln_list, chain_names=names)
    model = modelling.BuildFromRawModel(mhandle)
    ost.PopVerbosityLevel()
    return model
