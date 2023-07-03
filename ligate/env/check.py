import importlib
import logging
import os
import shutil
from importlib.metadata import version
from pathlib import Path

import click


def add_dir_to_path(directory: Path):
    directory = str(directory)
    path = os.environ.get("PATH", "")
    if directory not in path:
        os.environ["PATH"] = f"{path}:{directory}"


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


def check_openbabel_import() -> bool:
    prefix = f"Checking if `openbabel` can be imported:"
    try:
        import openbabel
        print_availability_status(prefix, True, ok="OK", notok="error")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="error")
        logging.error(error)
    return False


def check_gmxmmpba_import() -> bool:
    prefix = f"Checking if `GMXMMPBSA` can be imported:"
    try:
        import GMXMMPBSA
        print_availability_status(prefix, True, ok="OK", notok="error")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="error")
        logging.error(error)
    return False


def check_ambertools() -> bool:
    prefix = f"Checking if `AmberTools` is available:"
    antechamber_available = shutil.which("antechamber") is not None
    print_availability_status(prefix, antechamber_available, ok="OK", notok="antechamber not found")
    return antechamber_available


def check_python_package(name: str, expected_version: str) -> bool:
    prefix = f"Checking if `{name}` is installed:"
    try:
        module_version = version(name)
        if module_version == expected_version:
            print_availability_status(prefix, True, ok="OK", notok="error")
        else:
            print_availability_status(prefix, False, ok="OK",
                                      notok=f"expected version {expected_version}, found {module_version}")
        return True
    except BaseException as error:
        print_availability_status(prefix, False, ok="OK", notok="import error")
        logging.error(error)
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
    print_availability_status("Checking tmbed downloaded model:",
                              model_exists,
                              ok="OK",
                              notok="Model is not downloaded. Run `tmbed download`.")
    return model_exists
