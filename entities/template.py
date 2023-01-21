from dataclasses import dataclass
from typing import List

from bson import ObjectId

from entities.meal_item import MealItem


@dataclass
class Template:
    name: str
    description: str
    meal_items: List[MealItem]
    creator_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        meal_items = [MealItem.from_dict(meal_item) for meal_item in data["meal_items"]]
        return cls(data["name"], data["description"], meal_items, str(data["creator_id"]))

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "meal_items": [meal_item.to_dict() for meal_item in self.meal_items],
            "creator_id": ObjectId(self.creator_id)
        }
