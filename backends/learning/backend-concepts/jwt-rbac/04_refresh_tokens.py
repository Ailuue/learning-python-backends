"""
04_refresh_tokens.py — Access + Refresh Token Pattern
======================================================
A short-lived access token limits damage if it's stolen — it expires soon.
But you don't want users to log in every 15 minutes.

Solution: issue two tokens at login.

    Access token   (15 min TTL)  → used for every API request, stateless
    Refresh token  (7 day TTL)   → used only to get a new access token, stored server-side

When the access token expires the client calls /auth/refresh with the
refresh token to get a new pair. The old refresh token is immediately
invalidated (token rotation) — so if it was stolen, using it once reveals
the theft and revokes the attacker's session.

The refresh token is stored server-side so it can be revoked:
    • User logs out
    • User changes their password
    • Admin revokes a session
    • Suspicious activity detected

The `jti` (JWT ID) claim is a unique ID per token. The server stores
active JTIs. On refresh, it checks the JTI is still active before issuing
a new pair.

    POST /auth/login    → { access_token, refresh_token }
    GET  /me            → use access_token in Authorization header
    POST /auth/refresh  → { refresh_token } → new { access_token, refresh_token }
    POST /auth/logout   → revoke the refresh_token

Run:
    uvicorn 04_refresh_tokens:app --port 8000 --reload

Test:
    # Login — note both tokens
    curl -s -X POST http://localhost:8000/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "secret"}' | python -m json.tool

    # Use access_token to hit /me
    curl http://localhost:8000/me -H "Authorization: Bearer <access_token>"

    # Refresh — use the refresh_token, get back a new pair
    curl -s -X POST http://localhost:8000/auth/refresh \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "<refresh_token>"}' | python -m json.tool

    # The old refresh_token is now invalid (token rotation)
    curl -s -X POST http://localhost:8000/auth/refresh \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "<old_refresh_token>"}' | python -m json.tool

    # Logout — revokes the refresh token
    curl -X POST http://localhost:8000/auth/logout \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "<refresh_token>"}'

    # Using access_token in the Authorization header on /auth/refresh → rejected
    curl -s -X POST http://localhost:8000/auth/refresh \\
      -H "Content-Type: application/json" \\
      -d '{"refresh_token": "<access_token>"}' | python -m json.tool
"""

import time
import uuid
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI()

SECRET = "dev-secret-key-minimum-32-bytes!!"  # HS256 requires ≥32 bytes
ALGORITHM = "HS256"
ACCESS_TTL = 900          # 15 minutes
REFRESH_TTL = 7 * 86400   # 7 days

USERS = {
    "alice": {"password": "secret",  "role": "admin"},
    "bob":   {"password": "hunter2", "role": "viewer"},
}

# In production: store in Redis or a DB table with (jti, username, expires_at).
# Using a plain dict here so the demo has no dependencies beyond PyJWT.
active_refresh_tokens: dict[str, str] = {}  # jti → username

security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Token helpers ──────────────────────────────────────────────────────────────

def create_access_token(username: str, role: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": username, "role": role, "type": "access", "iat": now, "exp": now + ACCESS_TTL},
        SECRET,
        algorithm=ALGORITHM,
    )


def create_refresh_token(username: str) -> str:
    jti = uuid.uuid4().hex
    active_refresh_tokens[jti] = username
    now = int(time.time())
    return jwt.encode(
        {"sub": username, "jti": jti, "type": "refresh", "iat": now, "exp": now + REFRESH_TTL},
        SECRET,
        algorithm=ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expected an access token")
    return payload


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(body: LoginRequest):
    user = USERS.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return {
        "access_token": create_access_token(body.username, user["role"]),
        "refresh_token": create_refresh_token(body.username),
        "token_type": "bearer",
    }


@app.post("/auth/refresh")
def refresh(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired — please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Expected a refresh token")

    jti = payload.get("jti")
    if not isinstance(jti, str):
        # Rotation is keyed on jti — a refresh token without one can never be
        # revoked, so reject it rather than treating the lookup miss as expiry.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token has no jti claim")

    username = active_refresh_tokens.get(jti)
    if not username:
        # Token was already used or was revoked (e.g., by logout).
        # A legitimate client never reuses a refresh token, so this suggests
        # either a bug or a stolen token that was already rotated by the attacker.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token has been revoked")

    # Rotate: invalidate the old token before issuing the new pair
    del active_refresh_tokens[jti]

    user = USERS[username]
    return {
        "access_token": create_access_token(username, user["role"]),
        "refresh_token": create_refresh_token(username),
        "token_type": "bearer",
    }


@app.post("/auth/logout")
def logout(body: RefreshRequest):
    try:
        payload = jwt.decode(body.refresh_token, SECRET, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if isinstance(jti, str):
            active_refresh_tokens.pop(jti, None)
    except jwt.InvalidTokenError:
        pass  # already invalid — treat as a successful logout
    return {"status": "logged out"}


@app.get("/me")
def get_me(user: Annotated[dict, Depends(get_current_user)]):
    return {"username": user["sub"], "role": user["role"]}
