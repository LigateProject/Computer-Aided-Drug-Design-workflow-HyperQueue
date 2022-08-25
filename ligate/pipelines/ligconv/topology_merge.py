import logging

from hyperqueue import Job

from ...ligconv.pose import Pose, load_poses
from ...ligconv.topology import (
    merge_topologies,
    pos_res_for_ligand_to_fix_structure,
    write_topology_summary,
)
from ...utils.paths import GenericPath
from .common import Edge, LigConvContext, LigConvEdgeTaskState, LigConvLigandTaskState

logger = logging.getLogger(__name__)


def merge_topologies_task(
    job: Job, ctx: LigConvContext, task_state: LigConvLigandTaskState
) -> LigConvEdgeTaskState:
    edge_to_task = {}

    for edge in ctx.params.edges:
        task = job.function(
            merge_edge_topologies,
            args=(edge, ctx),
            deps=[
                task_state.get_ligand_task(edge.start_ligand_name()),
                task_state.get_ligand_task(edge.end_ligand_name()),
            ],
            name=f"merge_topologies_edge_{edge.start_ligand}_{edge.end_ligand}",
        )
        edge_to_task[edge] = task
    return LigConvEdgeTaskState(edge_to_task=edge_to_task)


def merge_edge_topologies(edge: Edge, ctx: LigConvContext):
    logging.debug(f"Merging topologies for edge {edge}")
    ligand_a = edge.start_ligand_name()
    ligand_b = edge.end_ligand_name()
    pose_a = find_best_pose_by_score(ctx.ligen_data.pose_file(ligand_a))
    pose_b = find_best_pose_by_score(ctx.ligen_data.pose_file(ligand_b))

    logging.debug(
        f"Best poses: A(ligand={ligand_a}, pose={pose_a.id}), "
        f"B(ligand={ligand_b}, pose={pose_b.id})"
    )

    edge_topology_dir = ctx.edge_topology_dir(edge)

    edge_merged_topology = ctx.edge_merged_topology_gro(edge)
    merge_topologies(
        ctx.ligand_topology_itp(ligand_a),
        ctx.ligand_pose_structure_mol2(ligand_a, pose_a.id),
        ctx.ligand_pose_structure_gro(ligand_a, pose_a.id),
        ctx.ligand_topology_itp(ligand_b),
        ctx.ligand_pose_structure_mol2(ligand_b, pose_b.id),
        ctx.ligand_pose_structure_gro(ligand_b, pose_b.id),
        edge_merged_topology,
        ctx.edge_merged_structure_gro(edge),
    )

    # TODO: generalize path to forcefield and topol_amber filename
    write_topology_summary(
        edge_topology_dir / "topol.top",
        ctx.edge_topology_ligand_in_water(edge),
        edge_topology_dir / "topol_amber.top",
        forcefield_path="amber99sb-ildn.ff",
    )

    pos_res_for_ligand_to_fix_structure(
        edge_merged_topology, edge_topology_dir / "posre_Ligand.itp"
    )


def find_best_pose_by_score(pose_file: GenericPath) -> Pose:
    poses = load_poses(pose_file)
    return max(poses, key=lambda pose: pose.ligen_score)
