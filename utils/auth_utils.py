from datetime import datetime, timedelta

import jwt
from passlib.hash import bcrypt

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 365
ALGORITHM = "HS256"
JWT_SECRET_KEY = "VERY_STRONG_AND_SECURE_JWT_SECRET_KEY"
COOKIE_NAME = "Authorization"
LOCAL_STORAGE_COOKIE_NAME = "token"


def get_password_hash(password: str) -> str:
    return bcrypt.using(rounds=12).hash(password)


def validate_password(password: str, password_hash: str) -> bool:
    return bcrypt.verify(password, password_hash)


def create_access_token(subject: str) -> str:
    expires_delta = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expires_delta, "sub": subject}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt
