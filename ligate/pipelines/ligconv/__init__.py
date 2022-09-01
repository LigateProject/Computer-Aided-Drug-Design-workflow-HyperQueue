from pathlib import Path

from hyperqueue import Job

from ..taskmapping import EdgeTaskMapping
from .ctx import LigConvContext
from .pose import prepare_ligand_poses_task
from .protein_topology import ProteinTopologyParams, create_protein_topology_task
from .structure_fix import fix_edge_structure_task
from .topology_merge import merge_topologies_task

DATA_DIR = Path(__file__).absolute().parent / "data"

FIX_STRUCTURE_MDP_FILE = DATA_DIR / "fixStructureOfHybridLigand.mdp"


def ligconv_pipeline(job: Job, ctx: LigConvContext) -> EdgeTaskMapping:
    sanity_check_ligconv(ctx)

    protein_topology_params = ProteinTopologyParams(forcefield=ctx.params.protein_ff)
    task = create_protein_topology_task(job, ctx, protein_topology_params)
    ligand_tasks = prepare_ligand_poses_task(job, [task], ctx=ctx)
    edge_tasks = merge_topologies_task(job, ctx, ligand_tasks)
    return fix_edge_structure_task(
        job,
        FIX_STRUCTURE_MDP_FILE,
        edge_tasks=edge_tasks,
        ctx=ctx,
    )


def sanity_check_ligconv(ctx: LigConvContext):
    """
    Performs a sanity check and prepares directories for the AWH pipeline into `workdir`.
    """
    for edge in ctx.params.edges:
        missing = []
        start = edge.start_ligand_name()
        if not ctx.ligen_data.has_ligand(start):
            missing.append(start)
        end = edge.end_ligand_name()
        if not ctx.ligen_data.has_ligand(end):
            missing.append(end)
        if missing:
            raise Exception(f"{edge} links ligand(s) that were not found: {missing}")
