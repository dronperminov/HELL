from enum import Enum


class BasePortionUnit(str, Enum):
    g100 = "100 г",
    ml100 = "100 мл",
    portion = "порция"

    @staticmethod
    def from_str(value: str) -> "BasePortionUnit":
        if value == BasePortionUnit.g100:
            return BasePortionUnit.g100

        if value == BasePortionUnit.ml100:
            return BasePortionUnit.ml100

        return BasePortionUnit.portion


class PortionUnit(str, Enum):
    g = "г",
    ml = "мл",
    tea_spoon = "ч.л.",
    table_spoon = "ст.л."
    portion = "порция"
    piece = "шт"
    slice = "ломтик"

    @staticmethod
    def from_str(value: str) -> "PortionUnit":
        if value == PortionUnit.g:
            return PortionUnit.g

        if value == PortionUnit.ml:
            return PortionUnit.ml

        if value == PortionUnit.tea_spoon:
            return PortionUnit.tea_spoon

        if value == PortionUnit.table_spoon:
            return PortionUnit.table_spoon

        if value == PortionUnit.portion:
            return PortionUnit.portion

        if value == PortionUnit.piece or value == "штука":
            return PortionUnit.piece

        if value == PortionUnit.slice or value == "ломтик":
            return PortionUnit.slice

        raise ValueError("Invalid PortionUnit")
