from pathlib import Path

from .path_provider import PathProvider


class ComplexOrLigand(PathProvider):
    def __init__(self, root: Path):
        super().__init__(root)

    @property
    def kind(self) -> str:
        raise NotImplementedError

    @property
    def corrected_box_gro(self) -> Path:
        raise NotImplementedError

    @property
    def editconf_input_gro(self) -> Path:
        raise NotImplementedError

    @property
    def solvated_gro(self) -> Path:
        raise NotImplementedError

    @property
    def topology_file(self) -> Path:
        raise NotImplementedError

    @property
    def add_ions_output(self) -> Path:
        raise NotImplementedError


class Complex(ComplexOrLigand):
    @property
    def kind(self) -> str:
        return "complex"

    @property
    def corrected_box_gro(self) -> Path:
        return self.file_path("correctBox_complex.gro")

    @property
    def editconf_input_gro(self) -> Path:
        return self.file_path("full.gro")

    @property
    def solvated_gro(self) -> Path:
        return self.file_path("solvated_complex.gro")

    @property
    def topology_file(self) -> Path:
        return self.file_path("topol_amber.top")

    @property
    def add_ions_output(self) -> Path:
        return self.file_path("addIons_complex.tpr")


class Ligand(ComplexOrLigand):
    @property
    def kind(self) -> str:
        return "ligand"

    @property
    def corrected_box_gro(self) -> Path:
        return self.file_path("correctBox_ligand.gro")

    @property
    def editconf_input_gro(self) -> Path:
        return self.file_path("merged.gro")

    @property
    def solvated_gro(self) -> Path:
        return self.file_path("solvated_ligand.gro")

    @property
    def topology_file(self) -> Path:
        return self.file_path("topol_ligandInWater.top")

    @property
    def add_ions_output(self) -> Path:
        return self.file_path("addIons_ligand.tpr")
