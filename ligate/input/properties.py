from . import ComputationTriple, ForceField


def protein_ff(input: ComputationTriple) -> str:
    return {ForceField.Amber: "amber"}[input.forcefield]
