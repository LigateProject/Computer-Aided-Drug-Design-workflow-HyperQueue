import dataclasses
import logging
from pathlib import Path

from hyperqueue.job import Job
from hyperqueue.task.task import Task

from ...ctx import Context
from ...input import ComputationTriple
from ...input.properties import get_cl, get_na
from ...mdp import render_mdp
from ...utils.io import delete_file, ensure_directory, replace_in_place
from ...utils.paths import GenericPath
from ...wrapper.gmx import GMX
from ..ligconv import LigConvContext
from ..ligconv.common import Edge
from .common import LigandOrProtein, LopWorkload, get_topname, topology_path


@dataclasses.dataclass
class MinimizationParams:
    steps: int = 100


@dataclasses.dataclass
class MinimizationPreparedData:
    mdp: Path


@dataclasses.dataclass
class MinimizationOutput:
    ligand_task: Task
    ligand_directory: Path
    protein_task: Task
    protein_directory: Path


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


def solvated_path(input: LopWorkload) -> Path:
    return input.directory / "solvated.gro"


def corrected_box_path(input: LopWorkload) -> Path:
    return input.directory / "correctBox.gro"


def solvate(ctx: Context, input: LopWorkload, triple: ComputationTriple):
    logging.info(f"Running solvate step on {input}, {triple}")

    solvated = solvated_path(input)
    topname = get_topname(input.lop, triple)

    ctx.gmx.execute(
        [
            "solvate",
            "-cp",
            corrected_box_path(input),
            "-cs",
            "spc216.gro",
            "-p",
            ctx.workdir / topology_path(topname),
            "-o",
            solvated,
        ]
    )
    delete_file(ctx.workdir / f"topology/#topol_{topname}.top.1#")
    replace_in_place(solvated, [("HOH", "SOL")])


def add_ions(
    ctx: Context,
    input: LopWorkload,
    triple: ComputationTriple,
    params: MinimizationParams,
) -> MinimizationPreparedData:
    logging.info(f"Running add_ions step on {input}, {triple}")

    topname = get_topname(input.lop, triple)
    topology = ctx.workdir / topology_path(topname)
    add_ions = input.directory / "addIons.tpr"

    generated_mdp = "generated_em_l0.mdp"
    render_mdp(ctx.mdpdir / "em_l0.mdp", generated_mdp, nsteps=params.steps)

    ctx.gmx.execute(
        [
            "grompp",
            "-f",
            generated_mdp,
            "-c",
            solvated_path(input),
            "-p",
            topology,
            "-o",
            add_ions,
            "-maxwarn",
            "2",
        ]
    )
    delete_file("mdout.mdp")
    ctx.gmx.execute(
        [
            "genion",
            "-s",
            add_ions,
            "-o",
            input.directory / "ions.gro",
            "-p",
            topology,
            "-pname",
            get_na(triple),
            "-nname",
            get_cl(triple),
            "-conc",
            "0.15",
            "-neutral",
        ],
        input=b"SOL\n",
    )
    delete_file(ctx.workdir / f"topology/#topol_{topname}.top.1#")
    delete_file(add_ions)

    return MinimizationPreparedData(mdp=Path(generated_mdp))


def energy_minimize(
    ctx: LigConvContext,
    input: LopWorkload,
    edge: Edge,
    prepared: MinimizationPreparedData,
):
    logging.info(f"Running energy_minimize step on {input}, {edge}")

    topname = get_topname(input.lop, edge)
    ctx.gmx.execute(
        [
            "grompp",
            "-f",
            prepared.mdp,
            "-c",
            input.directory / "ions.gro",
            "-p",
            ctx.workdir / topology_path(topname),
            "-o",
            input.directory / "EM.tpr",
            "-po",
            input.directory / "EMout.mdp",
            "-maxwarn",
            "2",
        ]
    )
    ctx.gmx.execute(["mdrun", "-v", "-deffnm", "EM"], workdir=input.directory)


def editconf_task(
    ctx: LigConvContext,
    gmx: GMX,
    edge: Edge,
    input_ligand: LopWorkload,
    input_protein: LopWorkload,
):
    def editconf(input: Path, output: Path):
        return gmx.execute(
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

    # Place the molecule of interest in a rhombic dodecahedron of the desired size (1.5 nm
    # distance to the edges)
    logging.info(f"Running editconf step on {input_ligand} and {input_protein}")
    editconf(ctx.edge_merged_structure_gro(edge), corrected_box_path(input_ligand))
    editconf(ctx.edge_full_structure_gro(edge), corrected_box_path(input_protein))
    modify_grofile_inplace(corrected_box_path(input_protein))


def energy_minimization_task(
    ctx: LigConvContext,
    edge: Edge,
    input: LopWorkload,
    params: MinimizationParams,
):
    solvate(ctx, input, edge)
    prepared = add_ions(ctx, input, edge, params)
    energy_minimize(ctx, input, edge, prepared)


def solvate_prepare(
    ctx: LigConvContext, edge: Edge, params: MinimizationParams, job: Job, gmx: GMX
) -> MinimizationOutput:
    edge_dir = ctx.edge_dir(edge)

    ligand_dir = ensure_directory(edge_dir / "ligand")
    protein_dir = ensure_directory(edge_dir / "protein")

    ligand_workload = LopWorkload(lop=LigandOrProtein.Ligand, directory=ligand_dir)
    protein_workload = LopWorkload(lop=LigandOrProtein.Protein, directory=protein_dir)
    task = job.function(
        editconf_task,
        args=(ctx, gmx, edge, ligand_workload, protein_workload),
        name=f"minimize-editconf-{edge.name()}",
    )

    ligand_task = job.function(
        energy_minimization_task,
        args=(ctx, edge, ligand_workload, params),
        deps=[task],
        name=f"minimize-ligand-{edge.name()}",
    )
    protein_task = job.function(
        energy_minimization_task,
        args=(ctx, edge, protein_workload, params),
        deps=[task],
        name=f"minimize-protein-{edge.name()}",
    )

    return MinimizationOutput(
        ligand_task=ligand_task,
        ligand_directory=ligand_dir,
        protein_task=protein_task,
        protein_directory=protein_dir,
    )
