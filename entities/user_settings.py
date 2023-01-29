from dataclasses import dataclass
from decimal import Decimal
from typing import Dict

from bson import ObjectId, Decimal128


@dataclass
class UserSettings:
    user_id: str
    theme: str
    limits: Dict[str, Decimal]
    add_limits: bool

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        theme = data.get("theme", "light")
        limits = {name: Decimal(str(value)) for name, value in data.get("limits", {}).items()}
        add_limits = data.get("add_limits", False)

        return cls(data["user_id"], theme, limits, add_limits)

    def to_dict(self) -> dict:
        return {
            "user_id": ObjectId(self.user_id),
            "theme": self.theme,
            "limits": {name: Decimal128(str(value)) for name, value in self.limits.items()},
            "add_limits": self.add_limits
        }
