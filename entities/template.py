from dataclasses import dataclass
from typing import List

from entities.meal_item import MealItem


@dataclass
class Template:
    name: str
    description: str
    meal_items: List[MealItem]
    creator_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        return cls(data["name"], data["description"], data["meal_items"], str(data["creator_id"]))
