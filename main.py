import logging
import os
import shutil

import click


@click.group()
def cli():
    pass


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
