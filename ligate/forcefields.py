import enum


class Forcefield(enum.Enum):
    Gaff2 = enum.auto()

    def to_str(self) -> str:
        if self == Forcefield.Gaff2:
            return "gaff"
        else:
            assert False
