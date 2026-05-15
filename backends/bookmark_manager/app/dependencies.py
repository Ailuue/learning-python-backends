from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.redis_client import get_redis
from app.security import TokenPayload, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]

BLOCKLIST_KEY_PREFIX = "blocklist:"


def blocklist_key(jti: str) -> str:
    return f"{BLOCKLIST_KEY_PREFIX}{jti}"


def get_current_token(token: TokenDep) -> TokenPayload:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    if get_redis().exists(blocklist_key(payload.jti)):
        raise credentials_exception
    return payload


TokenPayloadDep = Annotated[TokenPayload, Depends(get_current_token)]


def get_current_user(payload: TokenPayloadDep, session: SessionDep) -> User:
    user = session.exec(select(User).where(User.username == payload.sub)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
