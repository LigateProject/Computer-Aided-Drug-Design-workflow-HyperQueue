import logging
from pathlib import Path

import click

from ligate.env.check import check_ambertools, check_binary_exists, check_env_exists, \
    check_openbabel_import, \
    check_python_package, check_tmbed_model, check_gmxmmpba_import
from ligate.env.install import install_native_deps


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
    ok &= check_env_exists("GMXLIB")
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
    ok &= check_tmbed_model()
    ok &= check_ambertools()

    if ok:
        click.echo(click.style("All environment dependencies were found!", fg="green"))
    else:
        click.echo(click.style("Some environment dependencies were not found!", fg="red"))
        exit(1)


@cli.command()
@click.argument("build-dir", default="build")
def install(build_dir: str):
    env = install_native_deps(Path(build_dir))
    env_script = "awh-env.sh"
    with open("awh-env.sh", "w") as f:
        f.write(f"""
export PATH=$PATH:{':'.join(str(dir) for dir in env.binary_dirs)}
""".lstrip())
    print(f"Environment variables written into {env_script}. Run `source {env_script}` to load the environment.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(name)s:%(levelname)-4s %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
    cli()
