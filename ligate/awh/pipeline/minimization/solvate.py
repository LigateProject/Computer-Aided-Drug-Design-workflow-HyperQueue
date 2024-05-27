from pathlib import Path

from ...paths import ComplexOrLigand
from ....utils.io import check_file_nonempty, replace_in_place
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


def perform_editconf(gmx: Gromacs, input_gro: Path, output_gro: Path, workdir: Path):
    result = gmx.execute(
        [
            "editconf",
            "-f",
            input_gro,
            "-o",
            output_gro,
            "-bt",
            "dodecahedron",
            "-d",
            "1.5",
        ],
        workdir=workdir
    )
    check_file_nonempty(output_gro)
    return result


@trace_fn()
def solvate(input: ComplexOrLigand, gmx: Gromacs):
    # Place the molecule of interest in a rhombic dodecahedron of the desired size (1.5 nm
    # distance to the edges)
    box_gro = input.corrected_box_gro

    perform_editconf(
        gmx,
        input.editconf_input_gro,
        box_gro,
        workdir=input.path
    )

    # TODO: check thread usage
    # solvate with TIP3P water
    gmx.execute(
        [
            "solvate",
            "-cp", box_gro,
            "-cs", "spc216.gro",
            "-p", input.topology_file,
            "-o", input.solvated_gro,
        ],
        workdir=input.path
    )
    check_file_nonempty(input.solvated_gro)

    replace_in_place(input.solvated_gro, [("HOH", "SOL")])
