import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import ContextManager, List, Optional, Union

logger = logging.getLogger(__name__)

GenericPath = Union[Path, str]


@dataclass
class MappedFile:
    # Actual path where the input file appears or output file should appear
    target_path: Path
    # Path where the file is accessible in the container
    container_path: Path
    # Path where the file will be mounted from into the container
    host_path: Path
    input: bool


@contextlib.contextmanager
def ligen_container(container: GenericPath) -> ContextManager["LigenContainerContext"]:
    container = Path(container).absolute()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        ctx = LigenContainerContext(container, tmpdir)
        yield ctx


class LigenContainerContext:
    def __init__(self, container: Path, directory: Path):
        self.container = container
        self.apptainer_dir = ensure_directory(directory / "apptainer")
        self.files_container_dir = Path("/files")
        self.files_host_dir = ensure_directory(directory / "files")
        self.mapped_files: List[MappedFile] = []
        self.file_names = set()

    def map_file(self, path: Path, input: bool) -> Path:
        """
        Maps a file from the outside to the container.
        Returns a path to the file that will be accessible inside the container.

        Currently, this is implemented by copying the file into a temporary directory, but eventually
        it should be optimized so that apptainer overlays are used directly to access the input files.
        """
        path = path.absolute()
        name = path.name
        assert name not in self.file_names
        container_path = self.files_container_dir / name
        host_path = self.files_host_dir / name

        if input:
            logger.info(
                f"Copying {path} to {host_path} ({container_path} in container)"
            )
            shutil.copy(path, host_path)
        self.mapped_files.append(
            MappedFile(
                target_path=path,
                host_path=host_path,
                container_path=container_path,
                input=input,
            )
        )
        return container_path

    def map_input(self, path: Path) -> Path:
        return self.map_file(path, input=True)

    def map_output(self, path: Path) -> Path:
        return self.map_file(path, input=False)

    def run(self, command: str, input: Optional[bytes] = None):
        env = os.environ.copy()
        env["APPTAINER_TMPDIR"] = str(self.apptainer_dir)

        subprocess.check_output(
            [
                "apptainer",
                "exec",
                "--bind",
                f"{self.files_host_dir}:{self.files_container_dir}",
                str(self.container),
                "bash",
                "-c",
                f"""mpirun -np 1 --bind-to none {command}""",
            ],
            env=env,
            input=input,
        )

        # Copy output files from the tmpdir to their destination
        for file in self.mapped_files:
            if not file.input:
                host_path = file.host_path
                if not host_path.is_file():
                    raise Exception(f"Output file `{file.host_path}` not found")
                shutil.copy(host_path, file.target_path)


def ensure_directory(path: GenericPath) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path.absolute()
