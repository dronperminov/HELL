from dataclasses import dataclass
from decimal import Decimal
from entities.portion_unit import PortionUnit


@dataclass
class MealItem:
    food_id: str
    portion_size: Decimal
    portion_unit: PortionUnit

    @classmethod
    def from_dict(cls, data: dict) -> "MealItem":
        return cls(data["food_id"], Decimal(str(data["portion_size"])), PortionUnit(data["portion_unit"]))
