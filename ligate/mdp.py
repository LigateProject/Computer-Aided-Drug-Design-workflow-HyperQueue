import contextlib
import tempfile
from pathlib import Path
from typing import Generator

from jinja2 import Template

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
