"""
OAuth2 → JWT Session Bridge
==============================
OAuth2 tells you *who* the user is. It doesn't define how your app manages
its own sessions. This file shows the standard pattern for turning an OAuth2
identity into a JWT — the same kind your app would issue for any other login
method (password, magic link, SSO).

Why bridge to a JWT at all?
    The GitHub access token is scoped to the GitHub API. You can't use it
    to authenticate requests to *your* API — GitHub would be your auth server,
    not you. Instead:
      1. Verify identity via OAuth2 (GitHub/Google/etc.)
      2. Find or create the user in *your* database
      3. Issue *your own* JWT — identical to what you'd issue after a password login

    After step 3, your frontend doesn't know or care that OAuth2 was involved.
    All subsequent requests use your JWT, just like any other auth flow.

Endpoints:
    GET  /login/github              → redirect to GitHub
    GET  /auth/github/callback      → exchange code, upsert user, return JWT
    GET  /me                        → verify JWT, return user info
    GET  /protected                 → JWT-only endpoint

Setup:
    Same GitHub OAuth app as 02_github.py. Uses the same .env file.

Run:
    uvicorn 03_session:app --reload
    curl http://localhost:8000/login/github  (copy the Location URL, open in browser)
"""

import os
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

app = FastAPI(title="OAuth2 → JWT Bridge")
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"])

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=8)

oauth = OAuth()
oauth.register(
    name="github",
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email"},
)

# ---------------------------------------------------------------------------
# Simulated user store (replace with SQLAlchemy in production)
# ---------------------------------------------------------------------------

USERS: dict[str, dict] = {}   # keyed by "github:{github_id}"


def upsert_user(github_profile: dict) -> dict:
    """
    Find existing user or create a new one. Returns the internal user record.
    In production: session.merge() or INSERT … ON CONFLICT DO UPDATE.
    """
    provider_key = f"github:{github_profile['id']}"
    if provider_key not in USERS:
        USERS[provider_key] = {
            "id":         provider_key,
            "name":       github_profile.get("name") or github_profile["login"],
            "email":      github_profile.get("email"),
            "avatar_url": github_profile["avatar_url"],
            "provider":   "github",
        }
    return USERS[provider_key]


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_token(user: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["id"],      # subject — your internal user ID
        "name": user["name"],
        "iat": now,             # issued at
        "exp": now + TOKEN_TTL, # expiry
    }
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------------------------------------------------------------------
# Auth dependency — reusable across protected routes
# ---------------------------------------------------------------------------

bearer = HTTPBearer()

def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = decode_token(creds.credentials)
    user = USERS.get(payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/login/github")
async def login(request: Request):
    redirect_uri = request.url_for("callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/github/callback")
async def callback(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {e.error}")

    resp = await oauth.github.get("user", token=token)
    github_profile = resp.json()

    # Step 1: resolve the GitHub identity to your own user record.
    user = upsert_user(github_profile)

    # Step 2: issue your own JWT — from here, GitHub is out of the picture.
    access_token = create_token(user)

    # Return the token. In a real app you'd redirect to the frontend with
    # the token in a query param or a short-lived code, or set an HttpOnly cookie.
    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "expires_in":   int(TOKEN_TTL.total_seconds()),
        "user":         user,
        "note": "Pass this token as: Authorization: Bearer <token>",
    }


@app.get("/me")
async def me(user: dict = Depends(current_user)):
    """Requires a valid JWT — GitHub is no longer involved."""
    return user


@app.get("/protected")
async def protected(user: dict = Depends(current_user)):
    return {"message": f"Hello {user['name']}, you have access.", "user_id": user["id"]}
