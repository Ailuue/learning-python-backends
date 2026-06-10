"""
02_auth_flow.py — Login and Protected Routes
=============================================
The standard JWT auth flow:

    1. POST /auth/login
       Client sends credentials. Server validates them, mints a signed JWT,
       and returns it. The token contains the user's identity and role as claims.

    2. Client stores the token (localStorage, memory, cookie — each has trade-offs).

    3. Every subsequent request includes the token:
           Authorization: Bearer <token>

    4. GET /me (or any protected route)
       Server extracts the token from the header, verifies the signature and
       expiry, then trusts the claims without hitting the database again.
       This is what makes JWTs "stateless" — the server keeps no session state.

The FastAPI dependency system makes this clean: `Depends(get_current_user)`
on any route that requires authentication.

401 Unauthorized  → no token, expired token, invalid token
403 Forbidden     → valid token, but not allowed to do this action (see 03_rbac.py)

Run:
    uvicorn 02_auth_flow:app --port 8000 --reload

Test:
    # Login — copy the access_token from the response
    curl -s -X POST http://localhost:8000/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "secret"}' | python -m json.tool

    # Access a protected route
    curl http://localhost:8000/me -H "Authorization: Bearer <token>"

    # Wrong password → 401
    curl -s -X POST http://localhost:8000/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "wrong"}' | python -m json.tool

    # No token → 403 (FastAPI's HTTPBearer returns 403 when the header is missing)
    curl http://localhost:8000/me
"""

import time
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI()

SECRET = "dev-secret-key-minimum-32-bytes!!"  # HS256 requires ≥32 bytes; use secrets.token_hex(32) in prod
ALGORITHM = "HS256"
TOKEN_TTL = 3600  # 1 hour

# In a real app this is a database with hashed passwords (bcrypt/argon2).
# Plain-text passwords are only acceptable in a local demo.
USERS = {
    "alice": {"password": "secret",  "role": "admin"},
    "bob":   {"password": "hunter2", "role": "viewer"},
}

security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Token helpers ──────────────────────────────────────────────────────────────

def create_token(username: str, role: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": username, "role": role, "iat": now, "exp": now + TOKEN_TTL},
        SECRET,
        algorithm=ALGORITHM,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


# ── Dependency ─────────────────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """Extracts and validates the Bearer token. Inject with Depends()."""
    return decode_token(credentials.credentials)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(body: LoginRequest):
    user = USERS.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_token(body.username, user["role"])
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def get_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return {"username": current_user["sub"], "role": current_user["role"]}
