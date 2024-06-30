import shutil

from ..ligconv.common import LigandForcefield
from ..utils.paths import GenericPath
from .binarywrapper import execute_command


class Stage:
    def __init__(self):
        self.stage_path = shutil.which("stage.py")
        if self.stage_path is None:
            raise Exception("Could not find stage.py in PATH")

    def run(self, input: GenericPath, output: GenericPath, forcefield: LigandForcefield):
        return execute_command(
            [
                "python3",
                self.stage_path,
                "-i",
                input,
                "-o",
                output,
                "--forcefields",
                forcefield.to_str(),
            ]
        )
