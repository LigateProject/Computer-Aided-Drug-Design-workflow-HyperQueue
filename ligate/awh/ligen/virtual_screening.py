import json
import logging
from dataclasses import dataclass
from pathlib import Path

from .common import LigenTaskContext
from .container import ligen_container

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScreeningConfig:
    """
    Performs virtual screening on a set of ligands, outputs a CSV with scores per each ligand.
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
    Scores for input ligands in CSV format.
    """
    output_scores_csv: Path

    input_protein_name: str

    cores: int
    num_parser: int = 20
    num_workers_unfold: int = 20
    num_workers_docknscore: int = 100


def ligen_screen_ligands(ctx: LigenTaskContext, config: ScreeningConfig):
    logger.info(f"Starting virtual screening of {config.input_expanded_mol2}")
    with ligen_container(container=ctx.container_path) as ligen:
        input_smi = ligen.map_input(config.input_expanded_mol2)
        input_pdb = ligen.map_input(config.input_protein_pdb)
        input_mol2 = ligen.map_input(config.input_probe_mol2)
        output_csv = ligen.map_output(config.output_scores_csv)

        description = {
            "name": "vscreen",
            "pipeline": [
                {
                    "kind": "reader_mol2",
                    "name": "reader",
                    "input_filepath": str(input_smi),
                },
                {"kind": "parser_mol2", "number_of_workers": config.num_parser},
                {"kind": "bucketizer_ligand", "name": "bucketizer"},
                {"kind": "unfold", "cpp_workers": config.num_workers_unfold},
                {
                    "kind": "dock_n_score",
                    "wait_setup": "reader",
                    "number_of_restart": "256",
                    "clipping_factor": "256",
                    "scoring_functions": ["d22"],
                    "cpp_workers": config.num_workers_docknscore,
                },
                {
                    "kind": "writer_csv_bucket",
                    "name": "writer",
                    "wait_setup": "reader",
                    "output_filepath": str(output_csv),
                    "print_preamble": "1",
                    "csv_fields": ["SCORE_PROTEIN_NAME", "D22_SCORE"],
                    "separator": ",",
                },
                {"kind": "tracker_bucket", "wait_setup": "reader"},
                {"kind": "sink_bucket", "number_of_workers": "1"},
            ],
            "targets": [
                {
                    "name": config.input_protein_name,
                    "configuration": {
                        "input": {"format": "protein", "protein_path": str(input_pdb)},
                        "filtering": {
                            "algorithm": "probe",
                            "path": str(input_mol2),
                            "radius": "8",
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
