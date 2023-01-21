from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from bson import ObjectId, Decimal128

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

    def to_dict(self) -> dict:
        meal_dict = {
            "food_id": ObjectId(self.food_id),
            "portion_size": Decimal128(str(self.portion_size)),
            "portion_unit": f'{self.portion_unit}'
        }

        if self.group_id:
            meal_dict["group_id"] = ObjectId(self.group_id)
            meal_dict["group_name"] = self.group_name

        return meal_dict
