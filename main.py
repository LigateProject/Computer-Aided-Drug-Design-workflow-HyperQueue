import logging
from pathlib import Path

import click

from ligate.env.check import (
    check_ambertools,
    check_binary_exists,
    check_gmxmmpba_import,
    check_gromacs_env_exists,
    check_openbabel_import,
    check_promod3,
    check_python_package,
    check_tmbed_model,
)
from ligate.env.install import install_native_deps

ROOT_DIR = Path(__file__).absolute().parent
BUILD_DIR = ROOT_DIR / "build"


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
    ok &= check_python_package("ost", "1.0.0")
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
@click.argument("build-dir", default="build")
def install(build_dir: str):
    env = install_native_deps(Path(build_dir).absolute())
    env_script = Path("awh-env.sh").absolute()
    with open(env_script, "w") as f:
        print(
            f"export PATH=${{PATH}}:{':'.join(str(dir) for dir in env.binary_dirs)}",
            file=f,
        )
        for source in env.sources:
            print(f"source {source}", file=f)

        for (key, value) in env.env_vars.items():
            print(f'export {key}="{value}"', file=f)

    print(
        f"Environment variables written into {env_script}. Run `source {env_script}` to load the environment."
    )

    exec_script = Path("awh-exec.sh").absolute()
    with open(exec_script, "w") as f:
        print(f"source {env_script}", file=f)
        print(f'singularity exec {BUILD_DIR}/promod3.img "$@"', file=f)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    cli()
