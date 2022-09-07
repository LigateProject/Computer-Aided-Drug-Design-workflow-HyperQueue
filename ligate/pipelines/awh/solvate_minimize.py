import dataclasses
import logging
from pathlib import Path
from typing import List

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from ...ligconv.common import ProteinForcefield
from ...mdp import render_mdp
from ...utils.io import delete_file, replace_in_place
from ...utils.paths import GenericPath
from . import AWHContext
from .common import EM_L0_MDP
from .providers import AWHLigandOrProtein


@dataclasses.dataclass
class MinimizationParams:
    steps: int = 100


@dataclasses.dataclass
class MinimizationPreparedData:
    mdp: Path


@dataclasses.dataclass
class MinimizationOutput:
    ligand_task: Task
    protein_task: Task


def modify_grofile_inplace(path: GenericPath):
    replace_in_place(
        path,
        [
            ("1HD1", "HD11"),
            ("2HD1", "HD12"),
            ("3HD1", "HD13"),
            ("1HD2", "HD21"),
            ("2HD2", "HD22"),
            ("3HD2", "HD23"),
            ("1HE2", "HE21"),
            ("2HE2", "HE22"),
            ("1HG1", "HG11"),
            ("2HG1", "HG12"),
            ("3HG1", "HG13"),
            ("1HG2", "HG21"),
            ("2HG2", "HG22"),
            ("3HG2", "HG23"),
            ("1HH1", "HH11"),
            ("2HH1", "HH12"),
            ("1HH2", "HH21"),
            ("2HH2", "HH22"),
            ("1HH3", "HH31"),
            ("2HH3", "HH32"),
            ("3HH3", "HH33"),
            ("HOH      O", "HOH     OW"),
            ("HOH     H1", "HOH    HW1"),
            ("HOH     H2", "HOH    HW2"),
        ],
    )


def editconf_task(ctx: AWHContext):
    def editconf(input: Path, output: Path):
        return ctx.tools.gmx.execute(
            [
                "editconf",
                "-f",
                input,
                "-o",
                output,
                "-bt",
                "dodecahedron",
                "-d",
                "1.5",
            ]
        )

    ligand = ctx.edge_dir.ligand_dir
    protein = ctx.edge_dir.protein_dir

    # Place the molecule of interest in a rhombic dodecahedron of the desired size (1.5 nm
    # distance to the edges)
    logging.debug("Running editconf step")
    editconf(
        ctx.edge_dir.merged_structure_gro,
        ligand.corrected_box_gro,
    )
    editconf(ctx.edge_dir.full_structure_gro, protein.corrected_box_gro)
    modify_grofile_inplace(protein.corrected_box_gro)


def solvate(ctx: AWHContext, workload: AWHLigandOrProtein):
    solvated = workload.solvated_gro
    logging.debug(
        f"Running solvate step on {workload}, output will be written to {solvated}"
    )

    topology_file = workload.get_topology_file(ctx.edge_dir, ctx.protein_forcefield)
    ctx.tools.gmx.execute(
        [
            "solvate",
            "-cp",
            workload.corrected_box_gro,
            "-cs",
            "spc216.gro",
            "-p",
            topology_file,
            "-o",
            solvated,
        ]
    )
    replace_in_place(solvated, [("HOH", "SOL")])


def na_name(forcefield: ProteinForcefield) -> str:
    return {ProteinForcefield.Amber99SB_ILDN: "NA"}[forcefield]


def cl_name(forcefield: ProteinForcefield) -> str:
    return {ProteinForcefield.Amber99SB_ILDN: "CL"}[forcefield]


def add_ions(
    ctx: AWHContext,
    workload: AWHLigandOrProtein,
    params: MinimizationParams,
) -> MinimizationPreparedData:
    logging.debug(f"Running add_ions step on {workload}")

    add_ions_output = workload.file_path("addIons.tpr")

    generated_mdp = ctx.workdir / "generated_em_l0.mdp"
    render_mdp(EM_L0_MDP, generated_mdp, nsteps=params.steps)

    topology_file = workload.get_topology_file(ctx.edge_dir, ctx.protein_forcefield)
    ctx.tools.gmx.execute(
        [
            "grompp",
            "-f",
            generated_mdp,
            "-c",
            workload.solvated_gro,
            "-p",
            topology_file,
            "-o",
            add_ions_output,
            "-maxwarn",
            "2",
        ]
    )
    delete_file("mdout.mdp")

    ctx.tools.gmx.execute(
        [
            "genion",
            "-s",
            add_ions_output,
            "-o",
            workload.ions_gro,
            "-p",
            topology_file,
            "-pname",
            na_name(ctx.protein_forcefield),
            "-nname",
            cl_name(ctx.protein_forcefield),
            "-conc",
            "0.15",
            "-neutral",
        ],
        input=b"SOL\n",
    )
    delete_file(add_ions_output)
    return MinimizationPreparedData(mdp=generated_mdp)


def energy_minimize(
    ctx: AWHContext,
    workload: AWHLigandOrProtein,
    prepared: MinimizationPreparedData,
):
    logging.info(f"Running energy_minimize step on {workload}")

    ctx.tools.gmx.execute(
        [
            "grompp",
            "-f",
            prepared.mdp,
            "-c",
            workload.ions_gro,
            "-p",
            workload.get_topology_file(ctx.edge_dir, ctx.protein_forcefield),
            "-o",
            workload.em_tpr,
            "-po",
            workload.em_out_mdp,
            "-maxwarn",
            "2",
        ]
    )
    ctx.tools.gmx.execute(
        ["mdrun", "-v", "-deffnm", "EM", "-ntmpi", "4"], workdir=workload.path
    )


def energy_minimization_task_fn(
    ctx: AWHContext,
    workload: AWHLigandOrProtein,
    params: MinimizationParams,
):
    solvate(ctx, workload)
    prepared = add_ions(ctx, workload, params)
    energy_minimize(ctx, workload, prepared)


def solvate_prepare_task(
    job: Job,
    deps: List[Task],
    ctx: AWHContext,
    params: MinimizationParams,
) -> MinimizationOutput:
    task = job.function(
        editconf_task,
        args=(ctx,),
        name=f"minimize-editconf-{ctx.edge_name()}",
        deps=deps,
    )

    ligand_task = job.function(
        energy_minimization_task_fn,
        args=(ctx, ctx.edge_dir.ligand_dir, params),
        deps=[task],
        name=f"minimize-ligand-{ctx.edge_name()}",
    )
    protein_task = job.function(
        energy_minimization_task_fn,
        args=(ctx, ctx.edge_dir.protein_dir, params),
        deps=[task],
        name=f"minimize-protein-{ctx.edge_name()}",
    )

    return MinimizationOutput(
        ligand_task=ligand_task,
        protein_task=protein_task,
    )
