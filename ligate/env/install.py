import contextlib
import dataclasses
import subprocess
from pathlib import Path
from typing import List

import click

from .check import tmbed_model_exists, get_module_directory

CURRENT_DIR = Path(__file__).absolute().parent
ROOT_DIR = CURRENT_DIR.parent.parent
DEPS_DIR = ROOT_DIR / "deps"


@dataclasses.dataclass
class InstalledEnv:
    binary_dirs: List[Path] = dataclasses.field(default_factory=list)

    def add_bin_dir(self, path: Path):
        self.binary_dirs.append(path.absolute())


def install_native_deps(build_dir: Path) -> InstalledEnv:
    env = InstalledEnv()

    if not tmbed_model_exists():
        run_command("Downloading tmbed model", ["tmbed", "download"])

    install_dep("stage", DEPS_DIR / "stage.sh", build_dir)
    env.add_bin_dir(get_module_directory("openbabel") / "bin")
    env.add_bin_dir(build_dir / "stage" / "build" / "bin")
    return env


def install_dep(name: str, script: Path, build_dir: Path):
    run_command(f"Installing {click.style(name, fg='blue')}", [str(script), str(build_dir)])


@contextlib.contextmanager
def run_command(text: str, args: List[str]):
    click.echo(f"{text}...")
    try:
        subprocess.check_output(args)
        click.echo(f"{text} {click.style('succeeded', fg='green')}")
    except BaseException:
        click.echo(f"{text} {click.style('failed', fg='red')}")
        raise
