import dataclasses
from dataclasses import dataclass
from pathlib import Path
from typing import List

from hyperqueue import Job
from hyperqueue.ffi.protocol import ResourceRequest
from hyperqueue.task.task import Task

from .expansion import SubmittedExpansion, hq_submit_expansion
from ..ligen.common import LigenTaskContext
from ..ligen.docking import DockingConfig, ligen_dock
from ..ligen.expansion import ExpansionConfig
from ...utils.io import ensure_directory


@dataclass
class SubmittedDocking:
    config: DockingConfig
    task: Task


def hq_submit_ligand_docking(
    ctx: LigenTaskContext,
    config: DockingConfig,
    expansion_submit: SubmittedExpansion,
    job: Job,
) -> SubmittedDocking:
    task = job.function(
        ligen_dock,
        args=(
            ctx,
            config,
        ),
        deps=(expansion_submit.task,),
        name=f"docking-{config.output_poses_mol2.name}",
        resources=ResourceRequest(cpus=config.cores),
    )
    return SubmittedDocking(config=config, task=task)


@dataclasses.dataclass
class DockingPipelineConfig:
    input_smi: Path
    input_probe_mol2: Path
    input_protein: Path

    max_molecules_per_smi: int = 10


@dataclasses.dataclass
class SubmittedDockingPipeline:
    docked_mol2: Path
    tasks: List[Task]


def hq_submit_ligen_docking_workflow(
    ctx: LigenTaskContext,
    workdir: Path,
    config: DockingPipelineConfig,
    job: Job,
    deps: List[Task],
) -> SubmittedDockingPipeline:
    workdir_outputs = ensure_directory(workdir / "outputs")
    expanded_ligands_mol2 = workdir_outputs / "ligands.mol2"
    docked_mol2 = workdir_outputs / "docked.mol2"

    expansion_config = ExpansionConfig(
        id="expand-dock", input_smi=config.input_smi, output_mol2=expanded_ligands_mol2
    )
    expand_task = hq_submit_expansion(ctx, expansion_config, deps, job)

    docking_config = DockingConfig(
        input_probe_mol2=config.input_probe_mol2,
        input_protein_pdb=config.input_protein,
        input_expanded_mol2=expanded_ligands_mol2,
        input_protein_name="1CVU",
        output_poses_mol2=docked_mol2,
        cores=8,
    )
    task = hq_submit_ligand_docking(ctx, docking_config, expand_task, job).task
    return SubmittedDockingPipeline(docked_mol2=docked_mol2, tasks=[task])
