import contextlib
import dataclasses

from ...scripts import EM_L0_MDP
from ....mdp import rendered_mdp


@dataclasses.dataclass
class MinimizationParams:
    steps: int
    cores: int


@contextlib.contextmanager
def generate_mdp_for_minimization(params: MinimizationParams):
    with rendered_mdp(EM_L0_MDP, nsteps=params.steps) as em_l0_mdp:
        yield em_l0_mdp
