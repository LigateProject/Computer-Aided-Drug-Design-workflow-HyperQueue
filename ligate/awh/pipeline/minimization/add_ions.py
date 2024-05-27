from ...paths import ComplexOrLigand
from ...scripts import EM_L0_MDP
from ....mdp import rendered_mdp
from ....pipelines.awh import MinimizationParams
from ....utils.io import check_file_nonempty, delete_file
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@trace_fn()
def add_ions(input: ComplexOrLigand, params: MinimizationParams, gmx: Gromacs):
    with rendered_mdp(EM_L0_MDP, nsteps=params.steps) as em_l0_mdp:
        mdout = input.path / f"mdout_{input.kind}.mdp"
        gmx.execute([
            "grompp",
            "-f", em_l0_mdp,
            "-c", input.solvated_gro,
            "-r", input.solvated_gro,
            "-p", input.topology_file,
            "-o", input.add_ions_output,
            "-po", mdout,
            "-maxwarn", "2"
        ])
        check_file_nonempty(input.add_ions_output)
        delete_file(mdout)

        ions_output = f"ions_{input.kind}.gro"
        gmx.execute(
            [
                "genion",
                "-s", input.add_ions_output,
                "-o", ions_output,
                "-p", input.topology_file,
                "-pname", "NA",
                "-nname", "CL",
                "-neutral",
            ],
            input=b"SOL\n",
        )
        check_file_nonempty(ions_output)
        # delete_file(input.add_ions_output)
        # delete_file(input.solvated_gro)
