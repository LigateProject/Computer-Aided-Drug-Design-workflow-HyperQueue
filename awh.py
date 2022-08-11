import logging
import os
import shutil
from pathlib import Path

import click


@click.group()
def cli():
    pass


@cli.command()
def pipeline():
    from hyperqueue.cluster import LocalCluster, WorkerConfig
    from hyperqueue.job import Job
    from hyperqueue.visualization import visualize_job

    from ligate.ctx import Context
    from ligate.wrapper.gmx import GMX
    from ligate.input import ComputationTriple, ForceField, Protein
    from ligate.steps.analyze import analyze
    from ligate.steps.awh import AWHParams, awh
    from ligate.steps.equilibrate import EquilibrateParams, equilibrate
    from ligate.steps.pmx_input import PmxInputProvider
    from ligate.steps.solvate_minimize import MinimizationParams, solvate_prepare

    mdpdir = Path("mdp")
    workdir = Path("awh-job")
    gmx = GMX(Path("../libs/gromacs-2021.3/build/install/bin/gmx"))

    triple = ComputationTriple(
        protein=Protein.Bace,
        mutation="edge_CAT-13a_CAT-13m",
        forcefield=ForceField.Amber,
    )

    ctx = Context(
        workdir=workdir,
        mdpdir=mdpdir,
        gmx=gmx
    )

    with LocalCluster() as cluster:
        cluster.start_worker(WorkerConfig(cores=4))
        client = cluster.client()

        shutil.rmtree(workdir, ignore_errors=True)

        # Step 1: generate input files into `workdir`
        pmx_path = Path("../libs/pmx")
        pmx_provider = PmxInputProvider(pmx_path)
        pmx_provider.provide_input(triple, workdir)

        # Step 2: solvate minimize
        job = Job(workdir, default_env=dict(HQ_PYLOG="DEBUG"))
        minimization_params = MinimizationParams(steps=100)
        minimization_output = solvate_prepare(ctx, triple, minimization_params, job)

        # Step 3: equilibrate
        equilibrate_params = EquilibrateParams(steps=100)
        equilibrate_output = equilibrate(ctx, triple, equilibrate_params, minimization_output, job)

        # Step 4: AWH
        awh_params = AWHParams(steps=5000, diffusion=0.005, replicates=3)
        awh_output = awh(ctx, triple, awh_params, equilibrate_output, job)

        # Step 5: analyze
        analyze(ctx, awh_output, job)

        visualize_job(job, "job.dot")
        submitted_job = client.submit(job)
        client.wait_for_jobs([submitted_job])


def print_availability_status(prefix: str, available: bool, ok="found", notok="not found"):
    if available:
        click.echo(f"{prefix} {click.style(f'[{ok}]', fg='green')}")
    else:
        click.echo(f"{prefix} {click.style(f'[{notok}]', fg='red')}")


def check_binary_exists(binary: str) -> bool:
    prefix = f"Checking availability of executable `{binary}`:"
    if shutil.which(binary):
        print_availability_status(prefix, True)
        return True
    else:
        print_availability_status(prefix, False)
        return False


def check_env_exists(env: str) -> bool:
    prefix = f"Checking existence of environment variable `{env}`:"
    if env in os.environ:
        print_availability_status(prefix, True)
        return True
    else:
        print_availability_status(prefix, False)
        return False


def check_babel_import() -> bool:
    prefix = f"Checking if `openbabel` can be imported:"
    try:
        import openbabel
        print_availability_status(prefix, True, ok="OK", notok="error")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="error")
        logging.error(error)
    return False


def check_rdkit_import() -> bool:
    prefix = f"Checking if `rdkit` can be imported:"
    try:
        import rdkit
        print_availability_status(prefix, True, ok="OK", notok="error")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="error")
        logging.error(error)
    return False


@cli.command()
def check_env():
    """
    Performs a quick smoke test to check if the required binaries and libraries were found.
    """
    ok = True
    ok &= check_binary_exists("gmx")
    ok &= check_env_exists("GMXLIB")
    ok &= check_binary_exists("acpype")
    ok &= check_binary_exists("babel")
    ok &= check_babel_import()
    ok &= check_binary_exists("stage.py")
    ok &= check_rdkit_import()

    if ok:
        click.echo(click.style("All environment dependencies were found!", fg="green"))
    else:
        click.echo(click.style("Some environment dependencies were not found!", fg="red"))
        exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    cli()
