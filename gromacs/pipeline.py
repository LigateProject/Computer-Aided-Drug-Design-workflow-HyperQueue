import logging
import shutil
import subprocess
from pathlib import Path
from hyperqueue.client import Client

from src.ctx import Context, InputConfiguration
from src.parts.solvate_minimize import solvate_prepare

ROOT = Path(__file__).parents[1].absolute()
PMX_DIR = ROOT / "libs/pmx"
WORK_DIR = ROOT / "experiments"
MDP_DIR = ROOT / "libs/awh-benchmark/scripts/mdp"
GMX_BINARY = ROOT / "libs/gromacs-2021.3/build/install/bin/gmx"

ctx = Context(pmx_dir=PMX_DIR, root_dir=WORK_DIR, mdp_dir=MDP_DIR, gmx_binary=GMX_BINARY)
config = InputConfiguration(
    protein="bace",
    mutation="edge_CAT-13a_CAT-13m",
    forcefield="AMBER",
    itp_input_files=[...]
)

get_top_from_pmx("bace", "AMBER")
get_top_from_ligen(...)

# 1) MDP per stage
# 2) two .PDB files
# 3) 2 .top files (includes .itp files)
# Jinja templates

# Move GMX into submitted jobs
# 04 is the most expensive computation
# Ligand and protein is needed in step 05, before it's independent
# Ligand 5-10x faster than protein
# OpenMP threads max. 16
# MPI only for proteins, with GPUs smaller number of ranks
# GPUs should be configurable easily

shutil.rmtree("../experiments", ignore_errors=True)
script_dir = MDP_DIR.parent
subprocess.run("./setGlobalVariables.sh", cwd=script_dir, check=True)
subprocess.run("./01_assembleAndModifyInputFiles.sh", cwd=script_dir, check=True)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    client = Client()
    solvate_prepare(ctx, client, config)
