from hyperqueue import Job

from ...ligconv.gromacs import shift_last_gromacs_line, write_gro_complex_structure
from ...ligconv.topology import pos_res_for_ligand
from ...utils.io import delete_files, move_file
from ...utils.paths import GenericPath, active_workdir
from ..taskmapping import EdgeTaskMapping
from . import LigConvContext
from .common import Edge


def fix_edge_structure_task(
    job: Job,
    structure_mdp_file: GenericPath,
    edge_tasks: EdgeTaskMapping,
    ctx: LigConvContext,
) -> EdgeTaskMapping:
    state = {}
    for edge in ctx.params.edges:
        dependency = edge_tasks.get_edge_task(edge)
        state[edge] = job.function(
            fix_edge_structure,
            args=(edge, ctx, structure_mdp_file),
            deps=[dependency],
            name=f"fix_structure_edge_{edge.start_ligand}_{edge.end_ligand}",
        )
    return EdgeTaskMapping(edge_to_task=state)


def fix_edge_structure(edge: Edge, ctx: LigConvContext, structure_mdp_file: GenericPath):
    structure_merged = ctx.protein_dir.edge_dir(edge).merged_structure_gro
    structure_dir = structure_merged.parent
    tmp_structure = structure_dir / "merged_old.gro"
    move_file(structure_merged, tmp_structure)

    shift_last_gromacs_line(tmp_structure, 10)

    tpr_file = "merged.tpr"
    with active_workdir(structure_dir):
        ctx.tools.gmx.execute(
            [
                "grompp",
                "-f",
                structure_mdp_file,
                "-c",
                tmp_structure,
                "-r",
                tmp_structure,
                "-p",
                ctx.protein_dir.edge_dir(edge).topology_ligand_in_water,
                "-o",
                tpr_file,
            ]
        )
        ctx.tools.gmx.execute(["mdrun", "-deffnm", "merged"])
        delete_files(
            [
                tmp_structure,
                "mdout.mdp",
                tpr_file,
                "merged.trr",
                "merged.edr",
                "merged.log",
            ]
        )
        shift_last_gromacs_line(structure_merged, -10)

        conf_file = structure_dir / "conf.gro"
        write_gro_complex_structure(
            conf_file,
            structure_merged,
            ctx.protein_dir.edge_dir(edge).full_structure_gro,
        )

    topology_dir = ctx.protein_dir.edge_dir(edge).topology_dir
    pos_res_for_ligand(
        ctx.protein_dir.edge_dir(edge).merged_topology_itp,
        topology_dir / "posre_Ligand.itp",
    )
