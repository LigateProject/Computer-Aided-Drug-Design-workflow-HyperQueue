import dataclasses
import enum
import logging
from pathlib import Path
from typing import List

from .forcefields import FF, Forcefield
from .ligconv.gromacs import (
    construct_additional_gromacs_files,
    shift_last_gromacs_line,
    write_gro_complex_structure,
)
from .ligconv.pose import Pose, extract_and_clean_pose, load_poses
from .ligconv.topology import (
    merge_topologies,
    pos_res_for_ligand,
    pos_res_for_ligand_to_fix_structure,
    write_topology_summary,
)
from .utils.io import (
    check_dir_exists,
    copy_directory,
    delete_files,
    delete_path,
    ensure_directory,
    file_has_extension,
    iterate_directories,
    iterate_files,
    move_file,
    move_files,
)
from .utils.paths import GenericPath, normalize_path, use_dir
from .wrapper.babel import Babel
from .wrapper.gmx import GMX
from .wrapper.stage import Stage


@dataclasses.dataclass
class LigenOutputData:
    protein: str
    protein_file: Path
    ligand_dir: Path
    protein_ff_dir: Path
    ligands: List[Path]

    def pose_file(self, ligand: str) -> Path:
        return self.ligand_dir / ligand / "out_amber_pose_000001.txt"


def load_ligen_data(
    ligen_output_dir: GenericPath,
    protein: str,
    ligand: str,
    protein_file: str,
    protein_forcefield: str,
) -> LigenOutputData:
    """
    Loads data from a Ligen output directory.

    :param ligen_output_dir: Output directory produced by Ligen.
    :param protein: Name of the protein (e.g. `p38`).
    :param ligand: Name of the ligand (e.g. `ligands_gaff2`).
    :param protein_file: Protein file (e.g. `protein.pdb`).
    :param protein_forcefield: Name of the forcefield (e.g. `protein_amber`).
    """
    ligen_protein_dir = normalize_path(ligen_output_dir) / protein
    check_dir_exists(ligen_protein_dir)

    ligand_dir = ligen_protein_dir / ligand
    check_dir_exists(ligand_dir)
    protein_ff_dir = ligen_protein_dir / protein_forcefield
    check_dir_exists(protein_ff_dir)

    protein_file = protein_ff_dir / protein_file

    ligands = iterate_directories(ligand_dir)
    return LigenOutputData(
        protein=protein,
        ligand_dir=ligand_dir,
        protein_ff_dir=protein_ff_dir,
        ligands=ligands,
        protein_file=protein_file,
    )


@dataclasses.dataclass
class Edge:
    start_ligand: str
    end_ligand: str


@dataclasses.dataclass
class PipelineConfiguration:
    forcefield: Forcefield
    FF: FF
    pose_number: int
    edges: List[Edge]


@dataclasses.dataclass
class PipelineWorkdir:
    ligen_data: LigenOutputData
    configuration: PipelineConfiguration
    workdir: Path

    @property
    def forcefield_name(self) -> str:
        return self.configuration.forcefield.to_str()

    # Paths
    @property
    def protein_dir(self) -> Path:
        return self.workdir / self.ligen_data.protein

    @property
    def protein_topology_dir(self) -> Path:
        return self.protein_dir / self.forcefield_name / "topology"

    @property
    def protein_structure_dir(self) -> Path:
        return self.protein_dir / self.forcefield_name / "structure"

    def edge_topology_dir(self, edge: Edge) -> Path:
        return (
            self.protein_dir
            / edge_directory_name(edge)
            / self.forcefield_name
            / "topology"
        )

    def edge_structure_dir(self, edge: Edge) -> Path:
        return (
            self.protein_dir
            / edge_directory_name(edge)
            / self.forcefield_name
            / "structure"
        )

    def edge_merged_structure_gro(self, edge: Edge) -> Path:
        return self.edge_structure_dir(edge) / "merged.gro"

    def edge_topology_ligand_in_water(self, edge: Edge) -> Path:
        return self.edge_topology_dir(edge) / "topol_ligandInWater.top"

    def edge_merged_topology_gro(self, edge: Edge) -> Path:
        return self.edge_topology_dir(edge) / "merged.itp"

    def ligand_ff_dir(self, ligand: str) -> Path:
        return self.protein_dir / "ligands" / ligand / self.configuration.FF.to_str()

    def ligand_topology(self, ligand: str) -> Path:
        return self.ligand_ff_dir(ligand) / "topology" / "ligand.itp"

    def ligand_pose_dir(self, ligand: str, pose_id: int) -> Path:
        return self.ligand_ff_dir(ligand) / "poses" / str(pose_id)

    def ligand_pose_structure_gro(self, ligand: str, pose_id: int) -> Path:
        return self.ligand_pose_dir(ligand, pose_id) / "ligand.gro"

    def ligand_pose_structure_mol2(self, ligand: str, pose_id: int) -> Path:
        return self.ligand_pose_dir(ligand, pose_id) / "ligand.mol2"


def edge_directory_name(edge: Edge) -> str:
    return f"edge_{edge.start_ligand}_{edge.end_ligand}"


def prepare_directories(
    ligen_data: LigenOutputData,
    workdir: GenericPath,
    configuration: PipelineConfiguration,
) -> PipelineWorkdir:
    """
    Prepares directories for the AWH pipeline into `workdir`.
    """
    workdir = ensure_directory(workdir)
    protein_dir = ensure_directory(workdir / ligen_data.protein)

    ff_dir = ensure_directory(protein_dir / configuration.forcefield.to_str())
    ensure_directory(ff_dir / "topology")
    ensure_directory(ff_dir / "structure")

    ligands_dir = ensure_directory(protein_dir / "ligands")
    for ligand in ligen_data.ligands:
        ligand_name = ligand.name
        ligand_dir = ensure_directory(ligands_dir / ligand_name)
        ff_dir = ensure_directory(ligand_dir / configuration.FF.to_str())
        ensure_directory(ff_dir / "topology")
        ensure_directory(ff_dir / "poses")
        ensure_directory(ff_dir / "poses" / str(configuration.pose_number))

    for edge in configuration.edges:
        edge_dir = ensure_directory(protein_dir / edge_directory_name(edge))
        ff_dir = ensure_directory(edge_dir / configuration.forcefield.to_str())
        ensure_directory(ff_dir / "topology")
        ensure_directory(ff_dir / "structure")
    return PipelineWorkdir(
        ligen_data=ligen_data, configuration=configuration, workdir=workdir
    )


class ProteinTopologyForcefield(enum.Enum):
    Amber99SB_ILDN = 6


class ProteinTopologyWaterModel(enum.Enum):
    Tip3p = 1


@dataclasses.dataclass
class ProteinTopologyParams:
    forcefield: ProteinTopologyForcefield
    water_model: ProteinTopologyWaterModel


def create_protein_topology_step(
    gmx: GMX, workdir: PipelineWorkdir, params: ProteinTopologyParams
):
    with use_dir(workdir.protein_topology_dir):
        gmx.execute(
            ["pdb2gmx", "-f", workdir.ligen_data.protein_file, "-renum", "-ignh"],
            input=f"{params.forcefield.value}\n{params.water_model.value}".encode(),
        )
        move_file("conf.gro", workdir.protein_structure_dir)
    # Copy protein topology and structure to all edges
    for edge in workdir.configuration.edges:
        copy_directory(
            workdir.protein_topology_dir,
            workdir.edge_topology_dir(edge),
        )
        copy_directory(
            workdir.protein_structure_dir,
            workdir.edge_structure_dir(edge),
        )


def handle_poses_step(babel: Babel, stage: Stage, workdir: PipelineWorkdir):
    pose_number = workdir.configuration.pose_number
    # Parallelize over ligands
    for ligand in workdir.ligen_data.ligands:
        ligand_name = ligand.name
        ligand_dir = workdir.ligand_ff_dir(ligand_name)
        with use_dir(ligand_dir):
            filename = f"{ligand_name}_pose{pose_number}"
            pose_file = workdir.ligen_data.pose_file(ligand_name)
            cleaned_mol2 = ligand_dir / f"{filename}_clean.mol2"

            logging.debug(
                f"Extracting pose {pose_file}:{pose_number} into {cleaned_mol2}"
            )
            extract_and_clean_pose(pose_file, pose_number, cleaned_mol2, babel)

            stage_output = f"{filename}_stage"
            ff = workdir.configuration.FF
            logging.debug(
                f"Running stage on {cleaned_mol2}, output {stage_output}, forcefield {ff}"
            )
            stage.run(cleaned_mol2, stage_output, ff)

            pose_1_dir = ensure_directory(ligand_dir / "poses" / str(pose_number))
            # mv *.mol2 *.gro {pose_dir}
            files = list(
                iterate_files(
                    ligand_dir, filter=lambda p: file_has_extension(p, "mol2")
                )
            ) + list(
                iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "gro"))
            )
            move_files(files, pose_1_dir)

            topology_dir = ligand_dir / "topology"
            # mv *.itp *.pkl {topology_dir}
            files = list(
                iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "itp"))
            ) + list(
                iterate_files(ligand_dir, filter=lambda p: file_has_extension(p, "pkl"))
            )
            move_files(files, topology_dir)

            # Normalize filenames and put them into the correct directories
            ff_dir = ligand_dir / f"{stage_output}_{ff.to_str()}"
            move_files(iterate_files(ff_dir), topology_dir)
            move_file(
                topology_dir / f"{stage_output}.itp",
                workdir.ligand_topology(ligand_name),
            )
            move_file(
                topology_dir / f"posre_{stage_output}.itp",
                topology_dir / "posre_Ligand.itp",
            )
            move_file(
                pose_1_dir / f"{stage_output}.gro",
                workdir.ligand_pose_structure_gro(ligand_name, 1),
            )
            move_file(
                pose_1_dir / f"{stage_output}.mol2",
                workdir.ligand_pose_structure_mol2(ligand_name, 1),
            )
            delete_path(ff_dir)

            pose_1_ligand_gro = pose_1_dir / "ligand.gro"

            # Iterate through the remaining poses
            # Skips the first pose, we have already processed it
            poses = list(load_poses(pose_file))
            for (pose_num, pose) in enumerate(poses[1:], start=2):
                logging.debug(f"Handling pose {pose_file}:{pose_num}")
                extract_and_clean_pose(
                    pose_file,
                    pose_num,
                    workdir.ligand_pose_structure_mol2(ligand_name, pose_num),
                    babel,
                )
                construct_additional_gromacs_files(
                    pose,
                    pose_num,
                    pose_1_ligand_gro,
                    workdir.ligand_pose_structure_gro(ligand_name, pose_num),
                )
        # TODO: remove
        break


def find_best_pose_by_score(pose_file: GenericPath) -> Pose:
    poses = load_poses(pose_file)
    return max(poses, key=lambda pose: pose.ligen_score)


def format_ligand_name(ligand: str) -> str:
    return f"lig_{ligand}"


"""
Ligand A   Ligand B
|         /
|        /
|       /
|      /
   AB
    |
  merge
    |
  structure fix
"""


def merge_topologies_step(workdir: PipelineWorkdir):
    # Maybe parallelize over edges
    for edge in workdir.configuration.edges:
        logging.debug(f"Merging topologies for edge {edge}")
        ligand_a = format_ligand_name(edge.start_ligand)
        ligand_b = format_ligand_name(edge.end_ligand)
        pose_a = find_best_pose_by_score(workdir.ligen_data.pose_file(ligand_a))
        pose_b = find_best_pose_by_score(workdir.ligen_data.pose_file(ligand_b))

        logging.debug(
            f"Best poses: A(ligand={ligand_a}, pose={pose_a.id}), "
            f"B(ligand={ligand_b}, pose={pose_b.id})"
        )

        edge_topology_dir = workdir.edge_topology_dir(edge)

        edge_merged_topology = workdir.edge_merged_topology_gro(edge)
        merge_topologies(
            workdir.ligand_topology(ligand_a),
            workdir.ligand_pose_structure_mol2(ligand_a, pose_a.id),
            workdir.ligand_pose_structure_gro(ligand_a, pose_a.id),
            workdir.ligand_topology(ligand_b),
            workdir.ligand_pose_structure_mol2(ligand_b, pose_b.id),
            workdir.ligand_pose_structure_gro(ligand_b, pose_b.id),
            edge_merged_topology,
            workdir.edge_merged_structure_gro(edge),
        )

        # TODO: generalize
        write_topology_summary(
            edge_topology_dir / "topol.top",
            workdir.edge_topology_ligand_in_water(edge),
            edge_topology_dir / "topol_amber.top",
            forcefield_path="amber99sb-ildn.ff",
        )

        pos_res_for_ligand_to_fix_structure(
            edge_merged_topology, edge_topology_dir / "posre_Ligand.itp"
        )


def fix_structure_step(
    gmx: GMX, workdir: PipelineWorkdir, structure_mdp_file: GenericPath
):
    # Maybe parallelize here
    for edge in workdir.configuration.edges:
        structure_merged = workdir.edge_merged_structure_gro(edge)
        structure_dir = structure_merged.parent
        tmp_structure = structure_dir / "merged_old.gro"
        move_file(structure_merged, tmp_structure)

        shift_last_gromacs_line(tmp_structure, 10)

        tpr_file = "merged.tpr"
        with use_dir(structure_dir):
            gmx.execute(
                [
                    "grompp",
                    "-f",
                    structure_mdp_file,
                    "-c",
                    tmp_structure,
                    "-r",
                    tmp_structure,
                    "-p",
                    workdir.edge_topology_ligand_in_water(edge),
                    "-o",
                    tpr_file,
                ]
            )
            gmx.execute(["mdrun", "-deffnm", "merged"])
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
                conf_file, structure_merged, structure_dir / "full.gro"
            )

        topology_dir = workdir.edge_topology_dir(edge)
        pos_res_for_ligand(
            workdir.edge_merged_topology_gro(edge), topology_dir / "posre_Ligand.itp"
        )
