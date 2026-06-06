# OAuth2

## What is this?

Have you ever clicked "Login with Google" on a website? That's OAuth2.

**OAuth2** is a standard that lets users grant an application access to their account on another service — without giving that app their password. The app never sees your Google credentials. Google just tells the app "yes, this is Alice, and she said you can see her profile."

This solves a real problem: users have accounts everywhere (GitHub, Google, Spotify) and don't want to create yet another username and password for your app. OAuth2 lets you say "just use the account you already have."

## How it works (in plain English)

1. User clicks "Login with GitHub"
2. Your app redirects them to GitHub's login page
3. GitHub asks: "App X wants to see your profile. Allow?"
4. User clicks Allow
5. GitHub sends your app a short-lived **code** (not a password — just a one-time token)
6. Your app exchanges that code for an **access token** (server-to-server, using a secret key)
7. Your app uses the access token to ask GitHub "who is this user?"
8. GitHub responds with the user's profile (name, email, avatar)
9. Your app creates its own session — from here, GitHub is out of the picture

The key insight: your app never handles the user's GitHub password. GitHub handles authentication; your app just receives the result.

## What the files cover

| File | What it teaches |
|---|---|
| `01_concepts.py` | The raw mechanics — constructs auth URLs by hand, shows what each parameter does, demonstrates the CSRF protection (state parameter). No credentials needed to run. |
| `02_github.py` | A complete FastAPI app with GitHub login. Click a button, get redirected, come back logged in. Uses `authlib` to handle the protocol. |
| `03_session.py` | The bridge: after OAuth2 identifies the user, mint your *own* JWT. This is how OAuth2 connects to your existing auth system — from here your API works like any other JWT-protected app. |

## Setup

1. Go to [github.com/settings/applications/new](https://github.com/settings/applications/new)
2. Set **Homepage URL**: `http://localhost:8000`
3. Set **Callback URL**: `http://localhost:8000/auth/github/callback`
4. Copy the Client ID and Client Secret
5. Copy `.env.example` → `.env` and fill in the values

## How to run

```bash
pip install -r requirements.txt

# No credentials needed — just shows the mechanics:
python 01_concepts.py

# Full browser login flow:
uvicorn 02_github:app --reload
# Open http://localhost:8000 and click "Login with GitHub"

# OAuth2 → JWT bridge:
uvicorn 03_session:app --reload
# Visit http://localhost:8000/login/github in a browser
# Copy the returned JWT and use it:
# curl -H "Authorization: Bearer <token>" http://localhost:8000/me
```
