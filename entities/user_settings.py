from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

from bson import ObjectId, Decimal128


@dataclass
class UserSettings:
    user_id: str
    theme: str
    meal_types: List[str]
    limits: Dict[str, Decimal]
    add_limits: bool
    show_frequent: bool
    show_frequent_all: bool
    show_recent: bool
    show_recent_all: bool
    show_calories: bool

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        theme = data.get("theme", "light")
        meal_types = data.get("meal_types", [])
        limits = {name: Decimal(str(value)) for name, value in data.get("limits", {}).items()}
        add_limits = data.get("add_limits", False)
        show_frequent = data.get("show_frequent", True)
        show_frequent_all = data.get("show_frequent_all", True)
        show_recent = data.get("show_recent", True)
        show_recent_all = data.get("show_recent_all", True)
        show_calories = data.get("show_calories", True)

        return cls(data["user_id"], theme, meal_types, limits, add_limits, show_frequent, show_frequent_all, show_recent, show_recent_all, show_calories)

    def to_dict(self) -> dict:
        return {
            "user_id": ObjectId(self.user_id),
            "theme": self.theme,
            "meal_types": self.meal_types,
            "limits": self.limits_to_dict(),
            "add_limits": self.add_limits,
            "show_frequent": self.show_frequent,
            "show_frequent_all": self.show_frequent_all,
            "show_recent": self.show_recent,
            "show_recent_all": self.show_recent_all,
            "show_calories": self.show_calories
        }

    def limits_to_dict(self):
        return {name: Decimal128(str(value)) for name, value in self.limits.items()}
