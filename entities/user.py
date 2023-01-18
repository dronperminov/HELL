from dataclasses import dataclass


@dataclass
class User:
    username: str
    firstname: str
    lastname: str
    middlename: str
    password_hash: str
    admin: bool = False
