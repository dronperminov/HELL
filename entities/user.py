from dataclasses import dataclass
from typing import List

from bson import ObjectId


@dataclass
class User:
    username: str
    firstname: str
    lastname: str
    middlename: str
    password_hash: str
    friend_users: List[str]
    admin: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        username = data["username"]
        firstname = data.get("firstname", "")
        lastname = data.get("lastname", "")
        middlename = data.get("middlename", "")
        password_hash = data["password_hash"]
        friend_users = [str(user) for user in data.get("friend_users", [])]
        admin = data.get("admin", False)
        return cls(username, firstname, lastname, middlename, password_hash, friend_users, admin)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "middlename": self.middlename,
            "password_hash": self.password_hash,
            "friend_users": [ObjectId(user) for user in self.friend_users],
            "admin": self.admin
        }
