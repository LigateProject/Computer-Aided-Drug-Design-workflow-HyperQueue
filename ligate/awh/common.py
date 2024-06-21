from pathlib import Path

from .path_provider import PathProvider


class ComplexOrLigand(PathProvider):
    def __init__(self, root: Path):
        super().__init__(root)

    @property
    def edge(self) -> str:
        return self.root.parent.name

    @property
    def pose(self) -> str:
        return self.root.name

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
    def ions_output(self) -> Path:
        raise NotImplementedError

    @property
    def equiNVT(self) -> Path:
        raise NotImplementedError

    @property
    def production_tpr(self) -> Path:
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
    def ions_output(self) -> Path:
        return self.file_path("ions_complex.gro")

    @property
    def equiNVT(self) -> Path:
        return self.file_path("equiNVT_complex.tpr")

    @property
    def production_tpr(self) -> Path:
        return self.file_path("production_complex.tpr")


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
    def ions_output(self) -> Path:
        return self.file_path("ions_ligand.gro")

    @property
    def equiNVT(self) -> Path:
        return self.file_path("equiNVT_ligand.tpr")

    @property
    def production_tpr(self) -> Path:
        return self.file_path("production_ligand.tpr")
