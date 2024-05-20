
from ligate.awh.pipeline.equilibrate import EquilibrateParams, equilibrate
from ligate.wrapper.gromacs import Gromacs
from tests.utils.io import check_immutable_dir


def test_equilibrate(data_dir, tmp_path, gmx: Gromacs):
    input_dir = data_dir / "awh" / "1" / "02-ligen-to-gromacs-output"
    params = EquilibrateParams(
        file=input_dir / "equiNVT_ligand.tpr",
        workdir=tmp_path,
        cores=4
    )
    with check_immutable_dir(input_dir):
        equilibrate(params, gmx)
