import dataclasses
from pathlib import Path

from hyperqueue import Job

from ...wrapper.babel import Babel
from ...wrapper.gmx import GMX
from ...wrapper.stage import Stage
from .common import LigConvEdgeTaskState, LigConvParameters, LigenOutputData
from .pose import prepare_ligand_poses_task
from .protein_topology import ProteinTopologyParams, create_protein_topology_task
from .setup import prepare_ligconv_directories
from .structure_fix import fix_edge_structure_task
from .topology_merge import merge_topologies_task


@dataclasses.dataclass
class LigConvPipelineParameters:
    gmx: GMX
    babel: Babel
    stage: Stage

    workdir: Path

    parameters: LigConvParameters
    ligen_data: LigenOutputData


def ligconv_pipeline(
    job: Job, params: LigConvPipelineParameters
) -> LigConvEdgeTaskState:
    ligconv_ctx = prepare_ligconv_directories(
        params.ligen_data, params.workdir, params.parameters
    )

    protein_topology_params = ProteinTopologyParams(
        forcefield=params.parameters.protein_ff
    )
    task = create_protein_topology_task(
        job, ligconv_ctx, protein_topology_params, gmx=params.gmx
    )
    ligand_tasks = prepare_ligand_poses_task(
        job, [task], babel=params.babel, stage=params.stage, ctx=ligconv_ctx
    )
    edge_tasks = merge_topologies_task(job, ligconv_ctx, ligand_tasks)
    return fix_edge_structure_task(
        job,
        Path("ligen/scripts/fixStructureOfHybridLigand.mdp").absolute(),
        edge_tasks=edge_tasks,
        ctx=ligconv_ctx,
        gmx=params.gmx,
    )
