import dataclasses

from ...common import ComplexOrLigand
from ....mdp import generate_production_mdp
from ....utils.io import check_file_nonempty, delete_file
from ....wrapper.gromacs import Gromacs


@dataclasses.dataclass
class PrepareProductionSimulationParams:
    steps: int = -1


def prepare_production_simulation(
        item: ComplexOrLigand,
        params: PrepareProductionSimulationParams,
        gmx: Gromacs
):
    out_mdp = f"productionOut_{item.kind}.mdp"

    with generate_production_mdp(steps=params.steps) as mdp:
        gmx.execute([
            "grompp",
            "-f", mdp,
            "-c", item.equiNVT,
            "-p", item.topology_file,
            "-o", item.production_tpr,
            "-po", out_mdp,
            "-maxwarn", "2"
        ], workdir=item.path)
        check_file_nonempty(item.production_tpr)
        delete_file(item.file_path(out_mdp))
