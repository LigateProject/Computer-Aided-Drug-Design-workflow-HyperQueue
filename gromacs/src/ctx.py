import dataclasses
from pathlib import Path


@dataclasses.dataclass
class Context:
    pmx_dir: Path
    root_dir: Path
    mdp_dir: Path
    gmx_binary: Path

    def __post_init__(self):
        self.root_dir.mkdir(parents=True, exist_ok=True)


@dataclasses.dataclass
class InputConfiguration:
    protein: str
    mutation: str
    forcefield: str

    def directory(self, ctx: Context) -> Path:
        return ctx.root_dir / self.protein / self.mutation / self.forcefield

    def path(self, ctx: Context, path: Path) -> Path:
        return self.directory(ctx).joinpath(path)

    def protein_ff(self) -> str:
        if self.forcefield == "AMBER":
            return "amber"
        else:
            assert False

    def ligand_ff(self) -> str:
        if self.forcefield == "AMBER":
            return "gaff2"
        else:
            assert False

    def ff_name(self) -> str:
        if self.forcefield == "AMBER":
            return "amber99sb-star-ildn-mut"
        else:
            assert False

    def ff_path(self, ctx: Context):
        return ctx.pmx_dir / f"pmx/data/mutff45/{self.ff_name()}.ff"

    def na(self) -> str:
        if self.forcefield == "AMBER":
            return "NaJ"
        else:
            assert False

    def cl(self) -> str:
        if self.forcefield == "AMBER":
            return "ClJ"
        else:
            assert False
