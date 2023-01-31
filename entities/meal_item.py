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
    group_portion: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "MealItem":
        portion_size = Decimal(str(data["portion_size"]))
        portion_unit = PortionUnit(data["portion_unit"])
        return cls(data["food_id"], portion_size, portion_unit, str(data.get("group_id", "")), data.get("group_name"), data.get("group_portion"))

    def to_dict(self) -> dict:
        meal_dict = {
            "food_id": ObjectId(self.food_id),
            "portion_size": Decimal128(str(self.portion_size)),
            "portion_unit": f'{self.portion_unit}'
        }

        if self.group_id:
            meal_dict["group_id"] = ObjectId(self.group_id)
            meal_dict["group_name"] = self.group_name
            meal_dict["group_portion"] = self.group_portion

        return meal_dict
