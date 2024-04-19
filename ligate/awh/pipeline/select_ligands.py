import dataclasses
from pathlib import Path
from typing import List

from hyperqueue import Job
from hyperqueue.task.task import Task


@dataclasses.dataclass
class LigandSelectionConfig:
    input_smi: Path
    scores_csv: Path
    output_smi: Path
    n_ligands: int


def select_ligands(config: LigandSelectionConfig):
    """
    Selects N ligands from a SMILES file, based on scores in the provided CSV file.
    """
    import pandas as pd

    df = pd.read_csv(config.scores_csv)
    df = df.sort_values(by="D23RTMB_SCORE", ascending=False)
    selected = frozenset(df.iloc[: config.n_ligands]["NAME"])
    with open(config.output_smi, "w") as output:
        with open(config.input_smi) as input:
            for line in input:
                line = line.strip()
                if line in selected:
                    print(line, file=output)


def hq_submit_select_ligands(
    config: LigandSelectionConfig, job: Job, deps: List[Task]
) -> Task:
    return job.function(select_ligands, args=(config,), deps=deps)
