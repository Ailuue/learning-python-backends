from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
import jwt
from pydantic import BaseModel

from app.config import get_settings


class TokenPayload(BaseModel):
    sub: str
    jti: str
    exp: datetime


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire, "jti": str(uuid4())}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> TokenPayload | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return TokenPayload(
            sub=str(payload["sub"]),
            jti=str(payload["jti"]),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
    except (jwt.PyJWTError, KeyError, ValueError):
        return None
