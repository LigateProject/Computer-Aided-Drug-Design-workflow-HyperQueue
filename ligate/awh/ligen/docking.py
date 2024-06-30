import json
from dataclasses import dataclass
from pathlib import Path

from .common import LigenTaskContext
from .container import ligen_container


@dataclass(frozen=True)
class DockingConfig:
    """
    Performs docking of a set of ligands, outputs a MOL2 with docked poses.
    """

    """
    MOL2 crystal structure, serves as a probe for the protein PDB.
    """
    input_probe_mol2: Path
    """
    Input protein in PDB format.
    """
    input_protein_pdb: Path
    """
    Expanded SMILES file in MOL2 format.
    """
    input_expanded_mol2: Path
    """
    Docked poses for input ligands in MOL2 format.
    """
    output_poses_mol2: Path

    input_protein_name: str

    cores: int
    num_parser: int = 20
    num_workers_unfold: int = 20
    num_workers_dock: int = 32
    num_workers_score: int = 32


def ligen_dock(ctx: LigenTaskContext, config: DockingConfig):
    with ligen_container(container=ctx.container_path) as ligen:
        input_ligands_mol2 = ligen.map_input(config.input_expanded_mol2)
        input_pdb = ligen.map_input(config.input_protein_pdb)
        input_probe_mol2 = ligen.map_input(config.input_probe_mol2)
        output_mol2 = ligen.map_output(config.output_poses_mol2)

        description = {
            "name": "docking",
            "pipeline": [
                {
                    "kind": "reader_mol2",
                    "name": "reader",
                    "input_filepath": str(input_ligands_mol2),
                },
                {
                    "kind": "parser_mol2",
                    "name": "parser",
                    "number_of_workers": config.num_parser,
                },
                {"kind": "bucketizer_ligand", "name": "bucketizer_dock"},
                {"kind": "unfold", "cpp_workers": config.num_workers_unfold},
                {
                    "kind": "dock",
                    "name": "dock",
                    "number_of_restart": "256",
                    "clipping_factor": "256",
                    "cpp_workers": config.num_workers_dock,
                },
                {"kind": "bucketizer_ligand", "name": "bucketizer_score"},
                {
                    "kind": "score",
                    "name": "score",
                    "scoring_functions": ["d22"],
                    "cpp_workers": config.num_workers_score,
                },
                {
                    "kind": "filter_bucket",
                    "name": "ps",
                    "property_name": "D22_SCORE",
                    "keep_top": "20",
                },
                {
                    "kind": "d23rtmb_ligand",
                    "name": "d23",
                    "protein_filepath": str(input_pdb),
                    "probe_filepath": str(input_probe_mol2),
                    "prefix": "micromamba --name d23rtmb run -e BABEL_LIBDIR=/opt/micromamba/envs/d23rtmb/lib/openbabel/3.1.0",
                    "cuda": "0",
                },
                {
                    "kind": "filter_ligand",
                    "name": "ranker",
                    "property_name": "D23RTMB_SCORE",
                    "keep_top": "2",
                },
                {
                    "kind": "prop2name_ligand",
                    "name": "prop2name",
                    "properties_toadd": ["POSE_ID", "D23RTMB_SCORE"],
                },
                {
                    "kind": "writer_mol2_ligand",
                    "name": "writer",
                    "wait_setup": "reader",
                    "output_filepath": str(output_mol2),
                },
            ],
            "targets": [
                {
                    "name": config.input_protein_name,
                    "configuration": {
                        "input": {
                            "format": "protein",
                            "protein_path": str(input_pdb),
                        },
                        "filtering": {
                            "algorithm": "probe",
                            "path": str(input_probe_mol2),
                            "radius": "10",
                        },
                        "pocket_identification": {"algorithm": "caviar_like"},
                        "anchor_points": {
                            "algorithms": "maximum_points",
                            "separation_radius": "4",
                        },
                    },
                }
            ],
        }
        ligen.run(
            "ligen",
            input=json.dumps(description).encode("utf8"),
        )
