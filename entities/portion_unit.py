from enum import Enum


class BasePortionUnit(str, Enum):
    g100 = "100 г"
    ml100 = "100 мл"


class PortionUnit(str, Enum):
    g = "г"
    ml = "мл"
    tea_spoon = "ч.л."
    table_spoon = "ст.л."
    portion = "порция"
    piece = "шт"
    slice = "ломтик"
