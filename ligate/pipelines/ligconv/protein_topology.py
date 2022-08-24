import dataclasses

from hyperqueue import Job
from hyperqueue.task.task import Task

from ...ligconv.common import ProteinForcefield, WaterModel
from ...ligconv.topology import protein_ff_gromacs_code, water_model_gromacs_code
from ...utils.io import copy_directory, move_file
from ...utils.paths import use_dir
from ...wrapper.gmx import GMX
from . import LigConvContext


@dataclasses.dataclass
class ProteinTopologyParams:
    forcefield: ProteinForcefield
    water_model: WaterModel = WaterModel.Tip3p


def create_protein_topology_task(
    job: Job,
    ctx: LigConvContext,
    params: ProteinTopologyParams,
    gmx: GMX,
) -> Task:
    return job.function(create_protein_topology, args=(ctx, params, gmx))


def create_protein_topology(
    ctx: LigConvContext,
    params: ProteinTopologyParams,
    gmx: GMX,
):
    with use_dir(ctx.protein_topology_dir):
        gmx.execute(
            ["pdb2gmx", "-f", ctx.ligen_data.protein_file, "-renum", "-ignh"],
            input=f"{protein_ff_gromacs_code(params.forcefield)}\n"
            f"{water_model_gromacs_code(params.water_model)}".encode(),
        )
        move_file("conf.gro", ctx.protein_structure_dir)
    # Copy protein topology and structure to all edges
    for edge in ctx.params.edges:
        copy_directory(
            ctx.protein_topology_dir,
            ctx.edge_topology_dir(edge),
        )
        copy_directory(
            ctx.protein_structure_dir,
            ctx.edge_structure_dir(edge),
        )
