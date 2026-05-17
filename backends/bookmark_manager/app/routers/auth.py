import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select

from app.dependencies import (
    CurrentUserDep,
    SessionDep,
    TokenPayloadDep,
    blocklist_key,
)
from app.models import User
from app.rate_limit import limiter
from app.redis_client import get_redis
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserPublic
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, user_in: UserCreate, session: SessionDep) -> User:
    existing = session.exec(
        select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username)
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email or username already exists",
        )

    user = User(
        email=user_in.email,
        username=user_in.username,
        password_hash=hash_password(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    logger.info("Registered new user: %s", user.username)
    return user


@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> Token:
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning("Failed login attempt for username: %s", form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    token = create_access_token(subject=user.username)
    logger.info("Issued token for user: %s", user.username)
    return Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: TokenPayloadDep) -> None:
    """Revoke the caller's token by adding its jti to the Redis blocklist."""
    remaining = int((payload.exp - datetime.now(timezone.utc)).total_seconds())
    if remaining > 0:
        get_redis().setex(blocklist_key(payload.jti), remaining, "1")
    logger.info("User %s logged out (jti=%s)", payload.sub, payload.jti)


@router.get("/me", response_model=UserPublic)
def read_current_user(user: CurrentUserDep) -> User:
    return user
