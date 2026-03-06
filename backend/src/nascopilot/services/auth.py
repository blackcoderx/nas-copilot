from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from nascopilot.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    return jwt.encode({"sub": user_id, "exp": expire}, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return payload["sub"]
