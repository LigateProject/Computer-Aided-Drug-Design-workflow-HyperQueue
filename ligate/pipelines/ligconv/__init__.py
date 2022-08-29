import dataclasses
from pathlib import Path

from hyperqueue import Job

from ...wrapper.babel import Babel
from ...wrapper.gmx import GMX
from ...wrapper.stage import Stage
from ..taskmapping import EdgeTaskMapping
from .common import LigConvContext
from .pose import prepare_ligand_poses_task
from .protein_topology import ProteinTopologyParams, create_protein_topology_task
from .setup import sanity_check_ligconv
from .structure_fix import fix_edge_structure_task
from .topology_merge import merge_topologies_task


@dataclasses.dataclass
class LigConvPipelineParameters:
    gmx: GMX
    babel: Babel
    stage: Stage

    ctx: LigConvContext


def ligconv_pipeline(job: Job, params: LigConvPipelineParameters) -> EdgeTaskMapping:
    ctx = params.ctx
    sanity_check_ligconv(ctx)

    protein_topology_params = ProteinTopologyParams(forcefield=ctx.params.protein_ff)
    task = create_protein_topology_task(
        job, ctx, protein_topology_params, gmx=params.gmx
    )
    ligand_tasks = prepare_ligand_poses_task(
        job, [task], babel=params.babel, stage=params.stage, ctx=ctx
    )
    edge_tasks = merge_topologies_task(job, ctx, ligand_tasks)
    return fix_edge_structure_task(
        job,
        Path("ligen/scripts/fixStructureOfHybridLigand.mdp").absolute(),
        edge_tasks=edge_tasks,
        ctx=ctx,
        gmx=params.gmx,
    )
