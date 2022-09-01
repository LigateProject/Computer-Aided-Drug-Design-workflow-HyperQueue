import dataclasses


@dataclasses.dataclass
class ComputationTriple:
    protein: str
    mutation: str
    forcefield: str

    def __repr__(self) -> str:
        return f"(protein {self.protein}, mutation {self.mutation}, forcefield {self.forcefield})"
