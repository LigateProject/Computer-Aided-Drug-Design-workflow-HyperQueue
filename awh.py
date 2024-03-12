import logging
import shutil
from pathlib import Path

from ligate.awh.input import AWHInput
from ligate.awh.pipeline.check_protein import check_protein

DATA_DIR = Path("data").absolute()
WORKDIR = Path("workdir").absolute()

shutil.rmtree(WORKDIR, ignore_errors=True)
WORKDIR.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    input = AWHInput(input_dir=DATA_DIR / "protLig_benchmark_FEP" / "bace")

    check_protein(input.input_dir / "protein_amber" / "protein.pdb", WORKDIR)
