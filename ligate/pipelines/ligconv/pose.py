import itertools
import logging
from pathlib import Path
from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task

from ...ligconv.gromacs import construct_additional_gromacs_files
from ...ligconv.pose import extract_and_clean_pose, load_poses
from ...utils.io import (
    delete_path,
    file_has_extension,
    iterate_files,
    move_file,
    move_files,
)
from ...utils.paths import use_dir
from ..taskmapping import LigandTaskMapping
from . import LigConvContext

logger = logging.getLogger(__name__)


def prepare_ligand_poses_task(job: Job, deps: List[Task], ctx: LigConvContext) -> LigandTaskMapping:
    task_state = {}

    ligands = set(
        itertools.chain.from_iterable(
            (edge.start_ligand_name(), edge.end_ligand_name()) for edge in ctx.params.edges
        )
    )

    for ligand_name in ligands:
        ligand = ctx.ligen_data.ligand_path(ligand_name)
        task = job.function(
            prepare_ligand_poses,
            args=(ligand, ctx),
            deps=deps,
            name=f"prepare_ligand_poses_{ligand_name}",
        )
        task_state[ligand_name] = task
    return LigandTaskMapping(ligand_to_task=task_state)


def prepare_ligand_poses(ligand: Path, ctx: LigConvContext):
    ligand_name = ctx.ligen_data.ligand_name(ligand)
    ligand_dir = ctx.protein_dir.ligand_dir(ligand_name).path
    with use_dir(ligand_dir):
        # First, run stage to extract the topology of the first pose
        pose_number = 1
        filename = f"{ligand_name}_pose{pose_number}"
        pose_file = ctx.ligen_data.pose_file(ligand_name)
        cleaned_mol2 = ligand_dir / f"{filename}_clean.mol2"

        logger.debug(f"Extracting pose {pose_file}:{pose_number} into {cleaned_mol2}")
        extract_and_clean_pose(pose_file, pose_number, cleaned_mol2, ctx.tools.babel)

        stage_output = f"{filename}_stage"
        ligand_ff = ctx.params.ligand_ff
        logging.debug(
            f"Running stage on {cleaned_mol2}, output {stage_output}, ligand forcefield {ligand_ff}"
        )
        ctx.tools.stage.run(cleaned_mol2, stage_output, ligand_ff)

        pose_1_dir = ctx.protein_dir.ligand_dir(ligand_name).pose_dir(pose_number).path
        # mv *.mol2 *.gro {pose_dir}
        files = list(
            iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "mol2"))
        ) + list(iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "gro")))
        move_files(files, pose_1_dir)

        topology_dir = ctx.protein_dir.ligand_dir(ligand_name).topology_dir
        # mv *.itp *.pkl {topology_dir}
        files = list(
            iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "itp"))
        ) + list(iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "pkl")))
        move_files(files, topology_dir)

        # Normalize filenames and put them into the correct directories
        ligand_ff_dir = ligand_dir / f"{stage_output}_{ligand_ff.to_str()}"
        move_files(iterate_files(ligand_ff_dir), topology_dir)
        move_file(
            topology_dir / f"{stage_output}.itp",
            ctx.protein_dir.ligand_dir(ligand_name).topology_itp,
        )
        move_file(
            topology_dir / f"posre_{stage_output}.itp",
            topology_dir / "posre_Ligand.itp",
        )
        move_file(
            pose_1_dir / f"{stage_output}.gro",
            ctx.protein_dir.ligand_dir(ligand_name).pose_dir(1).structure_gro,
        )
        move_file(
            pose_1_dir / f"{stage_output}.mol2",
            ctx.protein_dir.ligand_dir(ligand_name).pose_dir(1).structure_mol2,
        )
        delete_path(ligand_ff_dir)

        pose_1_ligand_gro = pose_1_dir / "ligand.gro"

        # Iterate through the remaining poses
        # Stage is not executed again for them
        poses = list(load_poses(pose_file))
        for pose_num, pose in enumerate(poses[1:], start=2):
            logging.debug(f"Handling pose {pose_file}:{pose_num}")
            extract_and_clean_pose(
                pose_file,
                pose_num,
                ctx.protein_dir.ligand_dir(ligand_name).pose_dir(pose_num).structure_mol2,
                ctx.tools.babel,
            )
            construct_additional_gromacs_files(
                pose,
                pose_num,
                pose_1_ligand_gro,
                ctx.protein_dir.ligand_dir(ligand_name).pose_dir(pose_num).structure_gro,
            )
