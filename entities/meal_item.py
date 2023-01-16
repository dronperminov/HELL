from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from entities.portion_unit import PortionUnit


@dataclass
class MealItem:
    food_id: str
    portion_size: Decimal
    portion_unit: PortionUnit
    group_id: Optional[str]
    group_name: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "MealItem":
        return cls(data["food_id"], Decimal(str(data["portion_size"])), PortionUnit(data["portion_unit"]), str(data.get("group_id", "")), data.get("group_name"))
