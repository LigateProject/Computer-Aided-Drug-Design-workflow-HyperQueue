import contextlib
import tempfile
from pathlib import Path
from typing import Generator

from jinja2 import Template

from .awh.scripts import EM_L0_MDP, EQ_NVT_L0_MDP, PRODUCTION_MDP
from .utils.paths import GenericPath


def load_template(path: Path) -> Template:
    with open(path) as f:
        return Template(f.read())


def render_mdp(input: Path, output: GenericPath, **parameters):
    template = load_template(input)

    with open(output, "w") as f:
        f.write(template.render(**parameters))


@contextlib.contextmanager
def rendered_mdp(input: Path, **parameters) -> Generator[Path, None, None]:
    """
    Renders a MDP template into a temporary file and yields the filename.
    The file will be deleted once the context manager is closed.
    """
    template = load_template(input)

    with tempfile.TemporaryDirectory() as dir:
        path = Path(dir) / input.name
        with open(path, "w") as f:
            f.write(template.render(**parameters))
        yield path


@contextlib.contextmanager
def generate_em_l0_mdp(steps: int):
    with rendered_mdp(EM_L0_MDP, nsteps=steps) as mdp:
        yield mdp


@contextlib.contextmanager
def generate_eq_nvt_l0_mdp(steps: int):
    with rendered_mdp(EQ_NVT_L0_MDP, nsteps=steps) as mdp:
        yield mdp


@contextlib.contextmanager
def generate_production_mdp(steps: int):
    with rendered_mdp(PRODUCTION_MDP, nsteps=steps) as mdp:
        yield mdp
