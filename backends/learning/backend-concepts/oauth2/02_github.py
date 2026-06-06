"""
GitHub OAuth2 Login with FastAPI + Authlib
============================================
Implements the full Authorization Code flow from 01_concepts.py using the
authlib library, which handles state generation, storage, and token exchange.

Endpoints:
    GET /                       → login page (open in browser first)
    GET /login/github           → redirect to GitHub consent screen
    GET /auth/github/callback   → GitHub redirects here after user approves
    GET /me                     → returns the logged-in user (session cookie)
    GET /logout                 → clears the session

Setup (one-time):
    1. Go to github.com → Settings → Developer settings → OAuth Apps → New
    2. Application name:  anything
       Homepage URL:      http://localhost:8000
       Callback URL:      http://localhost:8000/auth/github/callback
    3. Copy Client ID and Client Secret into .env (see .env.example)

Run:
    uvicorn 02_github:app --reload
    Open http://localhost:8000 in a browser.

How authlib handles state
    authlib generates a random state value, stores it in the Starlette
    session (a signed cookie), and verifies it on the callback. You don't
    need to manage this yourself — but 01_concepts.py shows what it's doing
    under the hood.
"""

import os

from authlib.integrations.starlette_client import OAuth, OAuthError
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

app = FastAPI(title="GitHub OAuth2 Demo")

# Sessions store the state parameter between /login and /callback.
# In production use a long, random secret from your secrets manager.
app.add_middleware(SessionMiddleware, secret_key=os.environ["SECRET_KEY"])

# ---------------------------------------------------------------------------
# OAuth client registration
# ---------------------------------------------------------------------------

oauth = OAuth()
oauth.register(
    name="github",
    client_id=os.environ["GITHUB_CLIENT_ID"],
    client_secret=os.environ["GITHUB_CLIENT_SECRET"],
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={
        "scope": "read:user user:email",
        # Tell GitHub we want JSON back, not the default form-encoded response.
        "token_endpoint_auth_method": "client_secret_post",
    },
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if user:
        return f"""
        <h2>Logged in as {user['name']} (@{user['login']})</h2>
        <img src="{user['avatar_url']}" width="80" style="border-radius:50%">
        <p><a href="/logout">Log out</a></p>
        """
    return """
    <h2>GitHub OAuth2 Demo</h2>
    <a href="/login/github"
       style="display:inline-block;padding:10px 20px;background:#24292e;
              color:#fff;border-radius:6px;text-decoration:none;font-family:sans-serif">
      Login with GitHub
    </a>
    """


@app.get("/login/github")
async def login_github(request: Request):
    redirect_uri = request.url_for("callback_github")
    # authorize_redirect: builds the auth URL, stores state in session, redirects.
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/github/callback")
async def callback_github(request: Request):
    try:
        # authorize_access_token: verifies state, exchanges code for token.
        token = await oauth.github.authorize_access_token(request)
    except OAuthError as e:
        # State mismatch, expired code, user denied, etc.
        return HTMLResponse(f"<h3>OAuth error: {e.error}</h3><a href='/'>Try again</a>", status_code=400)

    # Use the token to fetch the user's GitHub profile.
    resp = await oauth.github.get("user", token=token)
    github_user = resp.json()

    # Store minimal profile in session — not the access token.
    # The access token is sensitive; session cookie is signed but readable.
    request.session["user"] = {
        "id":         github_user["id"],
        "login":      github_user["login"],
        "name":       github_user.get("name") or github_user["login"],
        "email":      github_user.get("email"),
        "avatar_url": github_user["avatar_url"],
    }

    return RedirectResponse("/")


@app.get("/me")
async def me(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse("/")
    return user


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")
