"""
03_rbac.py — Role-Based Access Control
========================================
Authentication answers "who are you?"
Authorization answers "what are you allowed to do?"

RBAC assigns users to roles, and each route requires a minimum role.
Because the role is stored as a claim inside the JWT, the server doesn't
need a database lookup on every request to know what the user can do.

Roles in this demo (ordered by privilege):
    viewer  → read only
    editor  → read + write
    admin   → read + write + delete

The key implementation idea is a *dependency factory*: `require_role("admin")`
returns a FastAPI dependency that rejects anyone below admin level. This keeps
authorization logic out of route handlers.

    401 Unauthorized  → no/invalid/expired token
    403 Forbidden     → valid token, but role is too low

Run:
    uvicorn 03_rbac:app --port 8000 --reload

Test:
    # Get tokens for three different roles
    curl -s -X POST http://localhost:8000/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "alice", "password": "secret"}' | python -m json.tool   # admin

    curl -s -X POST http://localhost:8000/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "bob", "password": "hunter2"}' | python -m json.tool    # editor

    curl -s -X POST http://localhost:8000/auth/login \\
      -H "Content-Type: application/json" \\
      -d '{"username": "carol", "password": "pass"}' | python -m json.tool     # viewer

    # viewer can read but not write or delete
    curl http://localhost:8000/articles              -H "Authorization: Bearer <viewer>"
    curl -X POST http://localhost:8000/articles      -H "Authorization: Bearer <viewer>"
    curl -X DELETE http://localhost:8000/articles/1  -H "Authorization: Bearer <viewer>"

    # editor can read and write but not delete
    curl -X POST http://localhost:8000/articles      -H "Authorization: Bearer <editor>"
    curl -X DELETE http://localhost:8000/articles/1  -H "Authorization: Bearer <editor>"

    # admin can do everything
    curl -X DELETE http://localhost:8000/articles/1  -H "Authorization: Bearer <admin>"
"""

import time
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

app = FastAPI()

SECRET = "dev-secret-key-minimum-32-bytes!!"  # HS256 requires ≥32 bytes
ALGORITHM = "HS256"

USERS = {
    "alice": {"password": "secret",  "role": "admin"},
    "bob":   {"password": "hunter2", "role": "editor"},
    "carol": {"password": "pass",    "role": "viewer"},
}

# Higher number = more privilege
ROLE_LEVEL = {"viewer": 0, "editor": 1, "admin": 2}

security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


def create_token(username: str, role: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {"sub": username, "role": role, "iat": now, "exp": now + 3600},
        SECRET,
        algorithm=ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    try:
        return jwt.decode(credentials.credentials, SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")


def require_role(minimum: str):
    """
    Dependency factory that enforces a minimum role level.

    Usage:
        @app.delete("/x")
        def delete(user = Depends(require_role("admin"))):
            ...

    Returns the verified user dict on success, raises 403 on failure.
    """
    def check(user: Annotated[dict, Depends(get_current_user)]) -> dict:
        user_level = ROLE_LEVEL.get(user.get("role", ""), -1)
        required_level = ROLE_LEVEL[minimum]
        if user_level < required_level:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Requires '{minimum}' role or above. You have '{user.get('role')}'.",
            )
        return user
    return check


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.post("/auth/login")
def login(body: LoginRequest):
    user = USERS.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return {"access_token": create_token(body.username, user["role"]), "token_type": "bearer"}


@app.get("/articles")
def list_articles(user: Annotated[dict, Depends(require_role("viewer"))]):
    return {"articles": ["Article 1", "Article 2"], "read_by": user["sub"]}


@app.post("/articles")
def create_article(user: Annotated[dict, Depends(require_role("editor"))]):
    return {"created": True, "by": user["sub"]}


@app.delete("/articles/{article_id}")
def delete_article(article_id: int, user: Annotated[dict, Depends(require_role("admin"))]):
    return {"deleted": article_id, "by": user["sub"]}
