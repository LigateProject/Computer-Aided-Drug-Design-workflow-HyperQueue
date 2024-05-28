from . import generate_mdp_for_minimization
from ...common import ComplexOrLigand
from ....pipelines.awh import MinimizationParams
from ....utils.io import check_file_nonempty, delete_file
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@trace_fn()
def add_ions(input: ComplexOrLigand, params: MinimizationParams, gmx: Gromacs):
    with generate_mdp_for_minimization(params) as mdp:
        mdout = input.path / f"mdout_{input.kind}.mdp"

        add_ions_output = input.file_path(f"addIons_{input.kind}.tpr")
        gmx.execute([
            "grompp",
            "-f", mdp,
            "-c", input.solvated_gro,
            "-r", input.solvated_gro,
            "-p", input.topology_file,
            "-o", add_ions_output,
            "-po", mdout,
            "-maxwarn", "2"
        ], workdir=input.path)
        check_file_nonempty(add_ions_output)
        delete_file(mdout)

        gmx.execute(
            [
                "genion",
                "-s", add_ions_output,
                "-o", input.ions_output,
                "-p", input.topology_file,
                "-pname", "NA",
                "-nname", "CL",
                "-neutral",
            ],
            input=b"SOL\n",
            workdir=input.path
        )
        check_file_nonempty(input.ions_output)
        delete_file(add_ions_output)
        delete_file(input.solvated_gro)
