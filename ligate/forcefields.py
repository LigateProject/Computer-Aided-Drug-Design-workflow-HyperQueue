import enum


class Forcefield(enum.Enum):
    Amber = enum.auto()

    def to_str(self) -> str:
        if self == Forcefield.Amber:
            return "AMBER"
        else:
            assert False


class FF(enum.Enum):
    Gaff2 = enum.auto()

    def to_str(self) -> str:
        if self == FF.Gaff2:
            return "gaff2"
        else:
            assert False
