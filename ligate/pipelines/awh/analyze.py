import dataclasses
import math
from pathlib import Path
from typing import List, Optional

import numpy as np
from hyperqueue.job import Job

from ...ctx import Context
from .awh import AWHOutput, AWHPartOutput
from .common import LigandOrProtein

# With nsteps = 5000 and dt = 0.002, you need TMAX = 5000 * 0.002 = 10.


def find_values_by_prefix(file: Path, prefixes: List[str], column=1) -> List[str]:
    """
    Goes through the input `file` and looks for lines starting with the given prefixes.
    Returns the selected column for each line with the given prefix.
    """
    values: List[Optional[str]] = [None] * len(prefixes)
    with open(file) as f:
        for line in f:
            line = line.strip().split()
            if not line:
                continue

            for index, prefix in enumerate(prefixes):
                if line[0] == prefix:
                    assert values[index] is None
                    values[index] = line[column]
    for value in values:
        assert value is not None
    return values


LAMBDA0 = "0.0000"
LAMBDA1 = "11.0000"


@dataclasses.dataclass
class AnalysisResult:
    error: float
    difference: float


def calculate_diff_error(ctx: Context, inputs: List[AWHPartOutput], lop: LigandOrProtein) -> AnalysisResult:
    items = [input for input in inputs if input.lop == lop]
    awh_directory = items[0].awh_directory
    tmax = 10  # TODO: calculate from input parameters, currently assumes 5000 AWH steps

    with open(awh_directory / "freeEnergySummaryStandardError.txt", "w") as f:
        f.write("results from PMF yielded by AWH:\n")

        # TODO: ask if the stddev should indeed be divided by `len(items) ** 2` and not just by
        # `len(items)`.
        stddev = 0
        deltas = []
        for run in items:
            run_dir = run.run_directory
            ctx.gmx.execute(
                [
                    "awh",
                    "-f",
                    run_dir / "awh.edr",
                    "-s",
                    run_dir / "awh.tpr",
                    "-o",
                    run_dir / "awh_pmf.xvg",
                    "-more",
                    "-b",
                    str(tmax),
                    "-e",
                    str(tmax),
                ]
            )
            output_file = run_dir / f"awh_pmf_t{tmax}.xvg"
            deltag0, deltag1 = find_values_by_prefix(output_file, [LAMBDA0, LAMBDA1])
            deltag = float(deltag1) - float(deltag0)
            f.write(f"{deltag:.4f}\n")
            deltas.append(deltag)

        average = np.mean(deltas)
        for delta in deltas:
            stddev += (average - delta) ** 2

        f.write(f"{average:.4f}\n")
        # stddev = np.std(deltas)
        # f.write(f"{stddev:.4f}\n")
        stddev = math.sqrt(stddev / (len(items) ** 2))
        f.write(f"{stddev:.4f}\n")

        """
        Ask about the calculation
        S2 0.0279894
        STDDEV 1:  0.0279894
        STDDEV 2:  .05576674
        DIFF1 0.0557667
        S1 0
        DIFF2 0.00310992
        S2 0.00310992
        ERROR:  .05576674
        """

        error = stddev * stddev
        if lop == LigandOrProtein.Ligand:
            difference = -average
        else:
            difference = average
    return AnalysisResult(error=error, difference=difference)


def analyze_task(ctx: Context, inputs: List[AWHPartOutput]):
    result_ligand = calculate_diff_error(ctx, inputs, LigandOrProtein.Ligand)
    result_protein = calculate_diff_error(ctx, inputs, LigandOrProtein.Protein)

    error = result_ligand.error + result_protein.error
    difference = result_ligand.difference + result_protein.difference

    with open(ctx.workdir / "freeEnergySummaryStandardError.txt", "w") as f:
        f.write("Results from PMF yielded by AWH:\n")
        f.write(f"Free energy difference: {difference:.4f} +- {error:.4f}\n")


def analyze(ctx: Context, awh_output: AWHOutput, job: Job):
    inputs = [item.output for item in awh_output.outputs]
    job.function(
        analyze_task,
        args=(ctx, inputs),
        deps=[item.task for item in awh_output.outputs],
        name="analysis",
    )
