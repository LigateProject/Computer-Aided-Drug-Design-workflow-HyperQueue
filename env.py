"""
This script serves for installing dependencies of the workflow and for checking if they
have been correctly installed.

It should not depend on any other external dependencies than click.
"""
import contextlib
import dataclasses
import importlib
import logging
import os
import shutil
import subprocess
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Callable, Dict, List, Optional

import click

ROOT_DIR = Path(__file__).absolute().parent
DEPS_DIR = ROOT_DIR / "deps"


@click.group()
def cli():
    pass


@cli.command()
def check_env():
    """
    Performs a quick smoke test to check if the required binaries and libraries were found.
    """

    ok = True
    ok &= check_binary_exists("gmx")
    ok &= check_gromacs_env_exists()
    ok &= check_gmxmmpba_import()
    ok &= check_openbabel_import()
    ok &= check_binary_exists("obabel")
    ok &= check_binary_exists("stage.py")
    ok &= check_python_package("rdkit", "2023.3.1")
    ok &= check_python_package("biopython", "1.81")
    ok &= check_python_package("rmsd", "1.5.1")
    ok &= check_python_package("pdb-tools", "2.5.0")
    ok &= check_python_package("parmed", "3.4.3+11.g41cc9ab1")
    ok &= check_python_package("acpype", "2022.7.21")
    ok &= check_binary_exists("acpype")
    ok &= check_python_package("tmbed", "1.0.0")

    def import_ost():
        pass

    ok &= check_python_package_import("ost", import_ost)
    ok &= check_tmbed_model()
    ok &= check_ambertools()
    ok &= check_promod3()

    if ok:
        click.echo(click.style("All environment dependencies were found!", fg="green"))
    else:
        click.echo(
            click.style("Some environment dependencies were not found!", fg="red")
        )
        exit(1)


@cli.command()
@click.argument("install-dir", default="installed", type=str)
@click.option("--build-dir", default="build", type=str)
@click.option("--env-script", default="env.sh", type=click.Path(file_okay=True))
@click.option("--verbose", default=False, is_flag=True)
def install(install_dir: str, build_dir: str, env_script: str, verbose: bool) -> None:
    click.echo("Installing workflow dependencies. This can take some time.")
    env = install_dependencies(
        Path(build_dir).absolute(), Path(install_dir).absolute(), verbose=verbose
    )
    with open(env_script, "w") as f:
        f.write(env.env_contents)

    click.echo(
        f"Environment variables written into {click.style(env_script, fg='green')}. Run {click.style(f'source {env_script}', fg='yellow')} to load the environment."
    )

    click.echo(
        f"Run {click.style(f'python3 {Path(__file__).name} check-env', fg='yellow')} to check if the environment was installed correctly."
    )


class InstallationEnv:
    def __init__(self, build_dir: Path, install_dir: Path, verbose: bool):
        self.build_dir = build_dir
        self.install_dir = install_dir
        self.verbose = verbose
        self.env_contents = ""

    def install_dep(self, name: str, script: Path):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_env = f.name
        run_command(
            f"Installing {click.style(name, fg='blue')}",
            [str(script), str(self.build_dir), str(self.install_dir)],
            env=dict(ENVIRONMENT_SCRIPT=str(temp_env)),
            verbose=self.verbose,
        )
        with open(temp_env) as f:
            env = f.read().strip()
            if env:
                self.env_contents += f"{env}\n"


def install_dependencies(
    build_dir: Path, install_dir: Path, verbose: bool
) -> InstallationEnv:
    env = InstallationEnv(build_dir=build_dir, install_dir=install_dir, verbose=verbose)
    env.install_dep("openmm", DEPS_DIR / "openmm.sh")
    env.install_dep("boost", DEPS_DIR / "boost.sh")
    env.install_dep("ost", DEPS_DIR / "ost.sh")
    env.install_dep("promod", DEPS_DIR / "promod.sh")
    env.install_dep("openbabel", DEPS_DIR / "openbabel.sh")
    env.install_dep("gromacs", DEPS_DIR / "gromacs.sh")
    env.install_dep("stage", DEPS_DIR / "stage.sh")

    # Download Tmbed model
    if not tmbed_model_exists():
        run_command("Downloading tmbed model", ["tmbed", "download"])

    return env


# # Ambertools
# if click.confirm(
#     "Do you want to install AmberTools? (Choose no if you have your own version)"
# ):
#     install_dep("AmberTools", DEPS_DIR / "ambertools-23.sh", build_dir)
#     env.add_source(build_dir / "amber22_src" / "install" / "amber.sh")


def run_command(
    text: str, args: List[str], env: Dict[str, str] | None = None, verbose: bool = False
):
    click.echo(f"{text}...")
    try:
        environment = os.environ.copy()
        if env is not None:
            environment.update(env)

        if verbose:
            subprocess.check_call(args, env=environment)
        else:
            output = subprocess.run(args, env=environment, capture_output=True)
            stdout = output.stdout.decode("utf-8")
            stderr = output.stderr.decode("utf-8")
            if output.returncode != 0:
                raise Exception(
                    f"Command {' '.join(args)} has failed\nStdout:\n{stdout}\n\nStderr:\n{stderr}"
                )

        click.echo(f"{text} {click.style('succeeded', fg='green')}")
    except BaseException:
        click.echo(f"{text} {click.style('failed', fg='red')}")
        raise


def add_dir_to_path(directory: Path):
    directory = str(directory)
    path = os.environ.get("PATH", "")
    if directory not in path:
        os.environ["PATH"] = f"{path}:{directory}"


def print_availability_status(
    prefix: str, available: bool, ok="found", notok="not found"
):
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


def check_env_exists(env: str, notok="missing") -> bool:
    prefix = f"Checking existence of environment variable `{env}`:"
    env_ok = env in os.environ
    print_availability_status(prefix, env_ok, notok=notok)
    return env_ok


def check_gromacs_env_exists() -> bool:
    return check_env_exists(
        "GMXLIB",
        notok="GMXLIB missing. Set it to <GROMACS_INSTALL_DIR>/share/gromacs/top",
    )


def check_openbabel_import() -> bool:
    prefix = "Checking if `openbabel` can be imported:"
    try:
        print_availability_status(prefix, True, ok="OK", notok="error")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="error")
        logging.error(error)
    return False


def check_gmxmmpba_import() -> bool:
    prefix = "Checking if `GMXMMPBSA` can be imported:"
    try:
        print_availability_status(prefix, True, ok="OK", notok="error")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="error")
        logging.error(error)
    return False


def check_ambertools() -> bool:
    prefix = "Checking if `AmberTools` is available:"
    antechamber_available = shutil.which("antechamber") is not None
    print_availability_status(
        prefix, antechamber_available, ok="OK", notok="antechamber not found"
    )
    return antechamber_available


def check_promod3() -> bool:
    prefix = "Checking if `ProMod3` is available:"
    pm_found = shutil.which("pm") is not None
    print_availability_status(prefix, pm_found, ok="OK", notok="pm not found")

    def import_promod3():
        pass

    promod_importable = check_python_package_import("promod3", import_promod3)
    return pm_found and promod_importable


def check_python_package(name: str, expected_version: str) -> bool:
    prefix = f"Checking if `{name}` is installed:"
    try:
        module_version = version(name)
        if module_version == expected_version:
            print_availability_status(prefix, True, ok="OK", notok="error")
        else:
            print_availability_status(
                prefix,
                False,
                ok="OK",
                notok=f"expected version {expected_version}, found {module_version}",
            )
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="import error")
        logging.error(error)
    return False


def check_python_package_import(name: str, import_callback: Callable[[], None]) -> bool:
    prefix = f"Checking if `{name}` can be imported:"
    try:
        import_callback()
        print_availability_status(prefix, True, ok="can be imported")
        return True
    except ImportError as error:
        logging.error(error)
        print_availability_status(prefix, False, notok="cannot be imported")
    return False


def get_module_directory(module: str) -> Path:
    module = importlib.import_module(module)
    return Path(module.__path__[0])


def tmbed_model_exists() -> bool:
    try:
        path = get_module_directory("tmbed") / "models" / "t5" / "pytorch_model.bin"
    except ModuleNotFoundError:
        return False
    return path.is_file()


def check_tmbed_model() -> bool:
    model_exists = tmbed_model_exists()
    print_availability_status(
        "Checking tmbed downloaded model:",
        model_exists,
        ok="OK",
        notok="Model is not downloaded. Run `tmbed download`.",
    )
    return model_exists


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    cli()
