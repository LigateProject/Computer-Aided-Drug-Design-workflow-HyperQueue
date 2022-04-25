import logging
import shutil
from pathlib import Path

from hyperqueue.cluster import LocalCluster, WorkerConfig
from hyperqueue.job import Job

from src.ctx import Context
from src.gmx import GMX
from src.input import ComputationTriple, ForceField, Protein
from src.steps.pmx_input import PmxInputProvider
from src.steps.solvate_minimize import solvate_prepare

# get_top_from_pmx("bace", "AMBER")
# get_top_from_ligen(...)

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

mdpdir = Path("mdp")
workdir = Path("work")
gmx = GMX(Path("../libs/gromacs-2021.3/build/install/bin/gmx"))

input = ComputationTriple(
    protein=Protein.Bace,
    mutation="edge_CAT-13a_CAT-13m",
    forcefield=ForceField.Amber,
)

ctx = Context(
    workdir=workdir,
    mdpdir=mdpdir,
    gmx=gmx
)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=4))
        client = cluster.client()

        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree("job-1", ignore_errors=True)

        # Step 1: generate input files into `workdir`
        pmx_path = Path("../libs/pmx")
        pmx_provider = PmxInputProvider(pmx_path)
        pmx_provider.provide_input(input, workdir)

        # Step 2: solvate minimize
        job = Job()
        deps = solvate_prepare(ctx, input, job)

        job_id = client.submit(job)
        client.wait_for_jobs(job_ids=[job_id])
