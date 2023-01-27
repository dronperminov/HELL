from dataclasses import dataclass

from bson import ObjectId


@dataclass
class UserSettings:
    user_id: str
    theme: str

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        return cls(data["user_id"], data.get("theme", "light"))

    def to_dict(self) -> dict:
        return {
            "user_id": ObjectId(self.user_id),
            "theme": self.theme
        }
