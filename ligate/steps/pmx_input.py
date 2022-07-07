from pathlib import Path
from typing import List

from ..input import ComputationTriple, ForceField, InputProvider, Mutation, Protein
from ..input.properties import protein_ff
from ..utils.io import (
    append_lines_to,
    append_to,
    copy_files,
    ensure_directory,
    iterate_file_lines,
    paths_in_dir,
    replace_in_place,
)

STRUCTURE_LIGAND_FILENAMES = ["mergedA.pdb", "mergedB.pdb"]
TOPOLOGY_LIGAND_FILENAMES = ["ffMOL.itp", "merged.itp"]


class PmxInputProvider(InputProvider):
    def __init__(self, pmx_path: Path):
        self.pmx_path = pmx_path.resolve()

    def provide_input(self, input: ComputationTriple, directory: Path):
        # TODO: thrombin logic
        assert input.protein == Protein.Bace
        assert input.forcefield == ForceField.Amber

        """
        Structure
        """
        structure_dir = ensure_directory(directory / "structure", clear=True)

        protein_dir = self.pmx_path / "protLig_benchmark" / protein_name(input.protein)

        # Copy PDB files to structure directory
        proteinff_dir = protein_dir / f"protein_{protein_ff(input)}"
        structure_protein_files = paths_in_dir(
            structure_protein_filenames(input), proteinff_dir
        )
        copy_files(structure_protein_files, structure_dir)

        transformation_dir = (
            protein_dir
            / f"transformations_{ligand_ff(input)}"
            / mutation_name(input.mutation)
        )
        structure_ligand_files = paths_in_dir(
            STRUCTURE_LIGAND_FILENAMES, transformation_dir
        )
        copy_files(structure_ligand_files, structure_dir)

        # Fuse all elements into one PDB file
        merged_pdb = structure_dir / "full.pdb"
        append_lines_to(
            iterate_file_lines(structure_protein_files[0]), merged_pdb, "ENDMDL"
        )
        append_lines_to(
            iterate_file_lines(structure_dir / "mergedA.pdb", skip=2),
            merged_pdb,
            "ENDMDL",
        )

        assert len(structure_protein_files) <= 3
        if len(structure_protein_files) > 2:
            append_lines_to(
                iterate_file_lines(structure_protein_files[2]), merged_pdb, "ENDMDL"
            )
        if len(structure_protein_files) > 1:
            append_lines_to(iterate_file_lines(structure_protein_files[1]), merged_pdb)

        """
        Topology
        """
        topology_dir = ensure_directory(directory / "topology", clear=True)

        # Copy files to topology directory
        topology_protein_files = topology_protein_filenames(input)
        copy_files(paths_in_dir(topology_protein_files, proteinff_dir), topology_dir)
        copy_files(
            paths_in_dir(TOPOLOGY_LIGAND_FILENAMES, transformation_dir), topology_dir
        )

        # .itp files
        # Add position restraints for protein and ligand
        topology_merged = topology_dir / "merged.itp"
        add_position_restraints(topology_merged, topology_dir / "posreLigand.itp")
        topology_chain1 = topology_dir / get_topology_chain_1(input)
        if input.protein == Protein.Bace:
            add_posres_include(topology_chain1, "posre.itp")
        add_posres_include(topology_merged, "posreLigand.itp")

        # Masses cannot be changed with AWH => modify ligand topology accordingly
        fix_masses_for_awh(topology_merged)

        # .top files
        ff_path = str(self.pmx_path / get_ff_path(input))
        replace_in_place(
            topology_dir / f"topol_{protein_ff(input)}.top",
            [(f"{get_ff_name(input)}.ff", ff_path)],
        )

        append_to(
            topology_dir / "topol_ligandInWater.top",
            f"""; Include forcefield parameters
#include "{ff_path}/forcefield.itp"
#include "ffMOL.itp"
#include "merged.itp"

; Include water topology
#include "{ff_path}/tip3p.itp"

; Include topology for ions
#include "{ff_path}/ions.itp"

[ system ]
; Name
ligand in water

[ molecules ]
; Compound        #mols
MOL 1
""",
        )


def fix_masses_for_awh(itp_file: Path):
    with open(itp_file) as f:
        lines = f.readlines()

    with open(itp_file, "w") as f:
        modify = False

        for line in lines:
            data = line.split()
            if modify and len(data) == 11:
                if float(data[7]) < float(data[10]):
                    mass = data[10]
                else:
                    mass = data[7]
                f.write(
                    "%6s%12s%7s%7s%7s%7s%11s%11s%12s%11s%11s\n"
                    % (
                        data[0],
                        data[1],
                        data[2],
                        data[3],
                        data[4],
                        data[5],
                        data[6],
                        mass,
                        data[8],
                        data[9],
                        mass,
                    )
                )
            else:
                f.write(line)
            if len(data) > 1 and data[1] == "atoms":
                modify = True
            elif len(data) > 1 and data[1] == "bonds":
                modify = False


def add_posres_include(file: Path, itp_file: str):
    append_to(
        file,
        f"""
; Include Position restraint file
#ifdef POSRES
#include "{itp_file}"
#endif
""",
    )


def add_position_restraints(input: Path, output: Path):
    with open(input) as f:
        with open(output, "w") as g:
            g.write("[ position_restraints ]\n")
            g.write("; atom  type      fx      fy      fz\n")

            check = -2

            for line in f:
                data = line.split()
                if check == 0:
                    if len(data) > 1:
                        if data[1] == "bonds":
                            check = -2
                        elif "h" not in data[1] and "H" not in data[1]:
                            g.write(
                                "%6d%6d%6d%6d%6d\n"
                                % (int(data[0]), 1, 1000, 1000, 1000)
                            )
                elif check == -1:
                    check = 0
                elif len(data) > 1:
                    if data[1] == "atoms":
                        check = -1


def get_ff_name(input: ComputationTriple) -> str:
    return {ForceField.Amber: "amber99sb-star-ildn-mut"}[input.forcefield]


def get_ff_path(input: ComputationTriple) -> str:
    """
    Returns path to FF relative to PMX directory.
    """
    return {ForceField.Amber: f"pmx/data/mutff45/{get_ff_name(input)}.ff"}[
        input.forcefield
    ]


def get_topology_chain_1(input: ComputationTriple) -> str:
    return {Protein.Bace: "topol.itp"}[input.protein]


def mutation_name(mutation: Mutation) -> str:
    return mutation


def protein_name(protein: Protein) -> str:
    return {Protein.Bace: "bace"}[protein]


def ligand_ff(input: ComputationTriple) -> str:
    return {ForceField.Amber: "gaff2"}[input.forcefield]


def structure_protein_filenames(input: ComputationTriple) -> List[str]:
    return {Protein.Bace: ["protein.pdb", "water.pdb"]}[input.protein]


def topology_protein_filenames(input: ComputationTriple) -> List[str]:
    return {Protein.Bace: ["posre.itp", f"topol_{protein_ff(input)}.top", "topol.itp"]}[
        input.protein
    ]
