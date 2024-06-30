import enum


class ProteinForcefield(enum.Enum):
    Amber99SB_ILDN = enum.auto()

    def to_str(self) -> str:
        if self == ProteinForcefield.Amber99SB_ILDN:
            return "amber"
        else:
            assert False


class LigandForcefield(enum.Enum):
    Gaff2 = enum.auto()

    def to_str(self) -> str:
        if self == LigandForcefield.Gaff2:
            return "gaff2"
        else:
            assert False


class WaterModel(enum.Enum):
    Tip3p = enum.auto()
