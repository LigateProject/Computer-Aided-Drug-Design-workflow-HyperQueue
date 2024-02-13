from pathlib import Path

from ...ligconv.common import ProteinForcefield
from ..ligconv.providers import LigConvEdgeDir
from ..path_provider import PathProvider


class AWHEdgeDir(LigConvEdgeDir):
    @staticmethod
    def from_ligconv_edge_dir(edge_dir: LigConvEdgeDir) -> "AWHEdgeDir":
        return AWHEdgeDir(edge_dir.root, edge_dir.edge)

    @property
    def ligand_dir(self) -> "AWHLigandDir":
        return AWHLigandDir(self.dir_path("ligand"))

    @property
    def protein_dir(self) -> "AWHProteinDir":
        return AWHProteinDir(self.dir_path("protein"))


class AWHLigandOrProtein(PathProvider):
    def __init__(self, root: Path):
        super().__init__(root)

    @property
    def corrected_box_gro(self) -> Path:
        return self.file_path("correctBox.gro")

    @property
    def solvated_gro(self) -> Path:
        return self.file_path("solvated.gro")

    def get_topology_file(self, edge_dir: AWHEdgeDir, protein_forcefield: ProteinForcefield):
        raise NotImplementedError

    @property
    def ions_gro(self) -> Path:
        return self.file_path("ions.gro")

    @property
    def em_tpr(self) -> Path:
        return self.file_path("EM.tpr")

    @property
    def em_out_mdp(self) -> Path:
        return self.file_path("EMout.mdp")

    @property
    def em_gro(self) -> Path:
        return self.file_path("EM.gro")

    @property
    def equi_dir(self) -> "AWHEquiDir":
        return AWHEquiDir(self.dir_path("equi_NVT"))

    def is_ligand(self) -> bool:
        raise NotImplementedError


class AWHLigandDir(AWHLigandOrProtein):
    def get_topology_file(self, edge_dir: AWHEdgeDir, protein_forcefield: ProteinForcefield):
        return edge_dir.topology_ligand_in_water

    def is_ligand(self) -> bool:
        return True


class AWHProteinDir(AWHLigandOrProtein):
    def get_topology_file(self, edge_dir: AWHEdgeDir, protein_forcefield: ProteinForcefield):
        return edge_dir.topology_forcefield(protein_forcefield)

    def is_ligand(self) -> bool:
        return False


class AWHEquiDir(PathProvider):
    @property
    def equi_nvt_tpr(self) -> Path:
        return self.file_path("equi_NVT.tpr")

    @property
    def equi_nvt_gro(self) -> Path:
        return self.file_path("equi_NVT.gro")

    @property
    def equi_nvtout_mdp(self) -> Path:
        return self.file_path("equi_NVTOUT.mdp")
