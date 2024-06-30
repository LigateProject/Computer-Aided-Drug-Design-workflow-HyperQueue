from . import MinimizationParams
from ...common import ComplexOrLigand
from ....mdp import generate_em_l0_mdp
from ....utils.io import check_file_nonempty, delete_files_filter, move_file
from ....utils.tracing import trace_fn
from ....wrapper.gromacs import Gromacs


@trace_fn()
def energy_minimize(
        input: ComplexOrLigand,
        params: MinimizationParams,
        gmx: Gromacs
):
    with generate_em_l0_mdp(params.steps) as mdp:
        minimized_em = input.file_path(f"EM_{input.kind}.tpr")
        mdpout = input.file_path(f"EMout_{input.kind}.mdp")
        gmx.execute(
            [
                "grompp",
                "-f", mdp,
                "-c", input.ions_output,
                "-r", input.ions_output,
                "-p", input.topology_file,
                "-o", minimized_em,
                "-po", mdpout,
                "-maxwarn", "2",
            ],
            workdir=input.path
        )
        check_file_nonempty(minimized_em)
    
        gmx.execute([
            "mdrun",
            "-v",
            "-deffnm", minimized_em.stem,
            "-ntmpi", "1",
            "-ntomp", params.cores
        ],
            workdir=input.path)
        minimized_gro = minimized_em.with_suffix(".gro")
        check_file_nonempty(minimized_gro)
        move_file(minimized_gro, input.ions_output)
        delete_files_filter(input.path, lambda p: p.name.startswith("EM") or p.name.startswith("#"))
