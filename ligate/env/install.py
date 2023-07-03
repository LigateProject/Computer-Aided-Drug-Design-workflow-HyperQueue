import contextlib
import dataclasses
import subprocess
from pathlib import Path
from typing import Dict, List

import click

from .check import tmbed_model_exists, get_module_directory

CURRENT_DIR = Path(__file__).absolute().parent
ROOT_DIR = CURRENT_DIR.parent.parent
DEPS_DIR = ROOT_DIR / "deps"


@dataclasses.dataclass
class InstalledEnv:
    binary_dirs: List[Path] = dataclasses.field(default_factory=list)
    env_vars: Dict[str, str] = dataclasses.field(default_factory=dict)
    sources: List[Path] = dataclasses.field(default_factory=list)

    def add_bin_dir(self, path: Path):
        self.binary_dirs.append(path.absolute())

    def add_env_var(self, key: str, value: str):
        assert key != "PATH"
        assert key not in self.env_vars
        self.env_vars[key] = value

    def add_source(self, source: Path):
        self.sources.append(source)


def install_native_deps(build_dir: Path) -> InstalledEnv:
    env = InstalledEnv()

    # Tmbed
    if not tmbed_model_exists():
        run_command("Downloading tmbed model", ["tmbed", "download"])

    # Stage
    install_dep("stage", DEPS_DIR / "stage.sh", build_dir)
    env.add_bin_dir(build_dir / "stage" / "build" / "bin")

    # OpenBabel
    env.add_bin_dir(get_module_directory("openbabel") / "bin")

    # GROMACS
    if click.confirm("Do you want to install GROMACS? (Choose no if you have your own version)"):
        install_dep("GROMACS", DEPS_DIR / "gromacs-2023.1.sh", build_dir)
        install_dir = build_dir / "gromacs-2023.1" / "install"
        env.add_env_var("GMXLIB", str(install_dir / "share" / "gromacs" / "top"))
        env.add_source(install_dir / "bin" / "GMXRC")

    # Ambertools
    if click.confirm("Do you want to install AmberTools? (Choose no if you have your own version)"):
        install_dep("AmberTools", DEPS_DIR / "ambertools-23.sh", build_dir)
        env.add_source(build_dir / "amber22_src" / "install" / "amber.sh")

    return env


def install_dep(name: str, script: Path, build_dir: Path):
    run_command(f"Installing {click.style(name, fg='blue')}", [str(script), str(build_dir)])


@contextlib.contextmanager
def run_command(text: str, args: List[str]):
    click.echo(f"{text}...")
    try:
        subprocess.check_call(args)
        click.echo(f"{text} {click.style('succeeded', fg='green')}")
    except BaseException:
        click.echo(f"{text} {click.style('failed', fg='red')}")
        raise
