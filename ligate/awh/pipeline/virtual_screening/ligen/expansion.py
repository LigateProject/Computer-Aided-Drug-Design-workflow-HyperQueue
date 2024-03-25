import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .common import LigenTaskContext
from .container import ligen_container
from .....utils.io import split_file_by_lines

logger = logging.getLogger(__name__)


@dataclass
class ExpansionConfig:
    """
    Describes the configuration of an expansion step performed by Ligen.
    Ligen takes input ligands in SMILES format and expands them to a MOL2 format.
    """

    id: str
    """
    SMILES file that contains several lines, each line describes a single ligand.
    """
    input_smi: Path
    """
    MOL2 file with the expanded output.
    """
    output_mol2: Path


def ligen_expand_smi(ctx: LigenTaskContext, config: ExpansionConfig):
    logger.info(f"Starting expansion of {config.input_smi}")
    with ligen_container(container=ctx.container_path) as ligen:
        input_smi = ligen.map_input(config.input_smi)
        output_mol2 = ligen.map_output(config.output_mol2)
        ligen.run(
            f"ligen-type < {input_smi} | ligen-coordinates | ligen-minimize > {output_mol2}",
        )
    logger.info(f"Finished expansion of {config.input_smi}")


def create_expansion_configs_from_smi(
    input_smi: Path, workdir_inputs: Path, workdir_outputs: Path, max_molecules: int
) -> List[ExpansionConfig]:
    """
    Splits a single SMI database into multiple files, so that each file has at most `max_molecules`
    molecules.
    The files will be stored into `workdir_inputs`.
    Returns a list of expansion configs for the created files.
    """
    configs = []
    basename = input_smi.stem
    for index, section in enumerate(
        split_file_by_lines(input_smi, max_lines=max_molecules)
    ):
        name = f"{basename}-{index}"
        input_path = workdir_inputs / f"{name}.smi"
        with open(input_path, "w") as f:
            f.write(section)
        output_path = workdir_outputs / f"{name}.mol2"
        configs.append(
            ExpansionConfig(id=name, input_smi=input_path, output_mol2=output_path)
        )
    return configs
