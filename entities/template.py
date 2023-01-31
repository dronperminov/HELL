from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Optional
from enum import Enum

from bson import ObjectId, Decimal128

from entities.meal_item import MealItem


class TemplateAvailability(str, Enum):
    me = "me"
    friends = "friends"
    users = "users"


@dataclass
class Template:
    name: str
    description: str
    meal_items: List[MealItem]
    availability: TemplateAvailability
    creator_id: str
    weight: Optional[Decimal]

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        meal_items = [MealItem.from_dict(meal_item) for meal_item in data["meal_items"]]
        availability = TemplateAvailability(data.get("availability", "me"))
        weight = Decimal(str(data.get("weight", "0")))
        return cls(data["name"], data["description"], meal_items, availability, str(data["creator_id"]), weight)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "meal_items": [meal_item.to_dict() for meal_item in self.meal_items],
            "availability": f'{self.availability}',
            "creator_id": ObjectId(self.creator_id),
            "weight": Decimal128(str(self.weight))
        }

    def get_food_ids(self) -> List[ObjectId]:
        return [ObjectId(meal_item.food_id) for meal_item in self.meal_items]

    def get_meal_info(self) -> Dict[ObjectId, MealItem]:
        return {ObjectId(meal_item.food_id): meal_item for meal_item in self.meal_items}
