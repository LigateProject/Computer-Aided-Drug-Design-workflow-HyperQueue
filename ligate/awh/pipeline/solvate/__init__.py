import typing
from pathlib import Path

from ....utils.io import check_file_nonempty, replace_in_place
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


ComplexOrLigand = typing.Literal["ligand", "complex"]


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
def solvate(pose_dir: Path, gmx: Gromacs, kind: ComplexOrLigand):
    suffix = "ligand" if kind == "ligand" else "complex"

    # Place the molecule of interest in a rhombic dodecahedron of the desired size (1.5 nm
    # distance to the edges)
    box_gro = pose_dir / f"correctBox_{suffix}.gro"

    gro_file = "merged.gro" if kind == "ligand" else "full.gro"
    perform_editconf(
        gmx,
        pose_dir / gro_file,
        box_gro,
        workdir=pose_dir
    )

    solvated_output = pose_dir / f"solvated_{suffix}.gro"

    topol_file = "topol_ligandInWater.top" if kind == "ligand" else "topol_amber.top"

    # TODO: check thread usage
    # solvate with TIP3P water
    gmx.execute(
        [
            "solvate",
            "-cp", box_gro,
            "-cs", "spc216.gro",
            "-p", pose_dir / topol_file,
            "-o", solvated_output,
        ],
        workdir=pose_dir
    )
    check_file_nonempty(solvated_output)

    replace_in_place(pose_dir / solvated_output, [("HOH", "SOL")])


# @trace_fn()
# def add_ions(pose_dir: Path):
#     add_ions_output = workload.file_path("addIons.tpr")
# 
#     generated_mdp = ctx.input_dir / "generated_em_l0.mdp"
#     render_mdp(EM_L0_MDP, generated_mdp, nsteps=params.steps)
# 
#     topology_file = workload.get_topology_file(ctx.edge_dir, ctx.protein_forcefield)
#     ctx.tools.gmx.execute(
#         [
#             "grompp",
#             "-f",
#             generated_mdp,
#             "-c",
#             workload.solvated_gro,
#             "-p",
#             topology_file,
#             "-o",
#             add_ions_output,
#             "-maxwarn",
#             "2",
#         ]
#     )
#     delete_file("mdout.mdp")
# 
#     ctx.tools.gmx.execute(
#         [
#             "genion",
#             "-s",
#             add_ions_output,
#             "-o",
#             workload.ions_gro,
#             "-p",
#             topology_file,
#             "-pname",
#             na_name(ctx.protein_forcefield),
#             "-nname",
#             cl_name(ctx.protein_forcefield),
#             "-conc",
#             "0.15",
#             "-neutral",
#         ],
#         input=b"SOL\n",
#     )
#     delete_file(add_ions_output)
#     return MinimizationPreparedData(mdp=generated_mdp)
