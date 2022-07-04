from . import ComputationTriple, ForceField


def protein_ff(input: ComputationTriple) -> str:
    return {ForceField.Amber: "amber"}[input.forcefield]


def get_na(input: ComputationTriple) -> str:
    return {ForceField.Amber: "NaJ"}[input.forcefield]


def get_cl(input: ComputationTriple) -> str:
    return {ForceField.Amber: "ClJ"}[input.forcefield]
