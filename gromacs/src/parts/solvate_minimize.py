from hyperqueue.client import Client
from hyperqueue.job import Job

from ..ctx import Context, InputConfiguration
from ..gmx import GMX
from ..io import replace_in_place, remove
from ..paths import use_dir


def modify_grofile_inplace(path: str):
    replace_in_place(path, [
        ("1HD1", "HD11"),
        ("2HD1", "HD12"),
        ("3HD1", "HD13"),
        ("1HD2", "HD21"),
        ("2HD2", "HD22"),
        ("3HD2", "HD23"),
        ("1HE2", "HE21"),
        ("2HE2", "HE22"),
        ("1HG1", "HG11"),
        ("2HG1", "HG12"),
        ("3HG1", "HG13"),
        ("1HG2", "HG21"),
        ("2HG2", "HG22"),
        ("3HG2", "HG23"),
        ("1HH1", "HH11"),
        ("2HH1", "HH12"),
        ("1HH2", "HH21"),
        ("2HH2", "HH22"),
        ("1HH3", "HH31"),
        ("2HH3", "HH32"),
        ("3HH3", "HH33"),
        ("HOH      O", "HOH     OW"),
        ("HOH     H1", "HOH    HW1"),
        ("HOH     H2", "HOH    HW2")
    ])


def solvated_path(directory: str) -> str:
    return f"{directory}/solvated.gro"


def topology_path(topname: str) -> str:
    return f"topology/topol_{topname}.top"


def solvate(gmx: GMX, directory: str, topname: str):
    solvated = solvated_path(directory)

    gmx.execute([
        "solvate",
        "-cp", f"{directory}/correctBox.gro",
        "-cs", "spc216.gro",
        "-p", topology_path(topname),
        "-o", solvated
    ])
    remove(f"topology/#topol_{topname}.top.1#")
    replace_in_place(solvated, [("HOH", "SOL")])


def add_ions(ctx: Context, config: InputConfiguration, gmx: GMX, directory: str, topname: str):
    topology = topology_path(topname)
    add_ions = f"{directory}/addIons.tpr"
    gmx.execute([
        "grompp",
        "-f", f"{ctx.mdp_dir}/em_l0.mdp",
        "-c", solvated_path(directory),
        "-p", topology,
        "-o", add_ions,
        "-maxwarn", "2"
    ])
    remove("mdout.mdp")
    gmx.execute([
        "genion",
        "-s", add_ions,
        "-o", f"{directory}/ions.gro",
        "-p", topology,
        "-pname", config.na(),
        "-nname", config.cl(),
        "-conc", "0.15",
        "-neutral"
    ], input=b"SOL\n")
    remove(f"topology/#topol_{topname}.top.1#")
    remove(add_ions)


def energy_minimize(ctx: Context, gmx: GMX, client: Client, directory: str, topname: str):
    gmx.execute([
        "grompp",
        "-f", str(ctx.mdp_dir / "em_l0.mdp"),
        "-c", f"{directory}/ions.gro",
        "-p", topology_path(topname),
        "-o", f"{directory}/EM.tpr",
        "-po", f"{directory}/EMout.mdp",
        "-maxwarn", "2"
    ])
    with use_dir(directory):
        job = Job()
        job.program([str(ctx.gmx_binary), "mdrun", "-v", "-deffnm", "EM"])
        id = client.submit(job)
        client.wait(id)


def solvate_prepare(ctx: Context, client: Client, config: InputConfiguration):
    gmx = GMX(ctx.gmx_binary)

    with use_dir(config.directory(ctx)):
        # Place the molecule of interest in a rhombic dodecahedron of the desired size (1.5 nm
        # distance to the edges)
        gmx.editconf("structure/mergedA.pdb", "ligand/correctBox.gro")
        gmx.editconf("structure/full.pdb", "protein/correctBox.gro")
        modify_grofile_inplace("protein/correctBox.gro")

        for (directory, topname) in (
                ("ligand", "ligandInWater"),
                ("protein", config.protein_ff())
        ):
            solvate(gmx, directory, topname)
            add_ions(ctx, config, gmx, directory, topname)
            energy_minimize(ctx, gmx, client, directory, topname)
