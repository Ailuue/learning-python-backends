"""
OAuth2 Authorization Code Flow — the mechanics
================================================
OAuth2 lets users grant your app access to their account on another service
(GitHub, Google) without giving you their password. Your app never sees their
credentials — it only receives a token scoped to what the user approved.

The Authorization Code flow (used by every major provider for web apps):

    Browser          Your App              GitHub
       │                 │                   │
       │  click login    │                   │
       │────────────────▶│                   │
       │                 │  build auth URL   │
       │  302 redirect   │──────────────────▶│  /login/oauth/authorize
       │◀────────────────│                   │
       │                 │                   │  show consent screen
       │                 │                   │  user approves
       │                 │                   │
       │  redirect with ?code=ABC&state=XYZ  │
       │◀────────────────────────────────────│
       │                 │                   │
       │  GET /callback?code=ABC&state=XYZ   │
       │────────────────▶│                   │
       │                 │  POST /access_token│
       │                 │  code=ABC         │
       │                 │  client_secret=…  │
       │                 │──────────────────▶│
       │                 │◀──────────────────│
       │                 │  {"access_token": │
       │                 │   "ghu_xxx…"}     │
       │                 │                   │
       │                 │  GET /user        │
       │                 │  Authorization: token ghu_xxx…
       │                 │──────────────────▶│
       │                 │◀──────────────────│
       │                 │  {user profile}   │
       │  set session    │                   │
       │◀────────────────│                   │

Why Authorization Code and not just the token?
    The code is short-lived (60 seconds) and single-use.
    The token exchange (step 4) requires the client_secret, which only the
    server knows. The browser never sees the token — it only saw the code.
    This protects against tokens leaking via browser history or referrer headers.

The state parameter (CSRF protection)
    Your app generates a random string, stores it in the user's session, and
    includes it in the auth URL. GitHub echoes it back in the callback. Your
    app verifies it matches. Without this, an attacker could craft a callback
    URL with their own code, tricking your server into linking their GitHub
    account to the victim's session.

Run:
    python 01_concepts.py
    (No credentials needed — just prints URLs and explains parameters.)
"""

import secrets
import urllib.parse


# ---------------------------------------------------------------------------
# Step 1: Build the authorization URL
# ---------------------------------------------------------------------------

def build_github_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    """Constructs the URL your app redirects the browser to."""
    params = {
        "client_id":    client_id,
        "redirect_uri": redirect_uri,
        "scope":        "read:user user:email",
        "state":        state,
        # "allow_signup": "false",  # prevent new GitHub account creation
    }
    return "https://github.com/login/oauth/authorize?" + urllib.parse.urlencode(params)


# ---------------------------------------------------------------------------
# Step 2: Parse the callback
# ---------------------------------------------------------------------------

def parse_callback(callback_url: str, expected_state: str) -> str:
    """
    Extracts the code from the callback URL and validates the state.
    In a real app this runs inside the /auth/github/callback route handler.
    """
    parsed = urllib.parse.urlparse(callback_url)
    params = urllib.parse.parse_qs(parsed.query)

    received_state = params.get("state", [None])[0]
    code = params.get("code", [None])[0]

    if received_state != expected_state:
        raise ValueError(
            f"State mismatch — possible CSRF attack!\n"
            f"  expected: {expected_state}\n"
            f"  received: {received_state}"
        )

    return code


# ---------------------------------------------------------------------------
# Step 3: Show the token exchange request (not actually executed)
# ---------------------------------------------------------------------------

def format_token_exchange(client_id: str, client_secret: str, code: str, redirect_uri: str) -> str:
    """
    Shows what the server-to-server token exchange looks like.
    This HTTP request happens on your backend — the browser never sees it.
    """
    return f"""POST https://github.com/login/oauth/access_token
Content-Type: application/json
Accept: application/json

{{
  "client_id":     "{client_id}",
  "client_secret": "{client_secret}",
  "code":          "{code}",
  "redirect_uri":  "{redirect_uri}"
}}

Response:
{{
  "access_token": "ghu_16C7e42F292c6912E7710c838347Ae178B4a",
  "token_type":   "bearer",
  "scope":        "read:user,user:email"
}}"""


# ---------------------------------------------------------------------------
# Step 4: Show what the user profile fetch looks like
# ---------------------------------------------------------------------------

def format_user_fetch(access_token: str) -> str:
    return f"""GET https://api.github.com/user
Authorization: token {access_token}

Response (abbreviated):
{{
  "id":         1234567,
  "login":      "alice",
  "name":       "Alice Smith",
  "email":      "alice@example.com",
  "avatar_url": "https://avatars.githubusercontent.com/u/1234567"
}}"""


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=== OAuth2 Authorization Code Flow — mechanics ===\n")

    CLIENT_ID = "Ov23liABCDEF123456"          # from github.com/settings/applications
    CLIENT_SECRET = "abc123…"                   # kept SECRET on the server
    REDIRECT_URI = "http://localhost:8000/auth/github/callback"

    # Step 1
    state = secrets.token_urlsafe(16)   # random, unguessable
    auth_url = build_github_auth_url(CLIENT_ID, REDIRECT_URI, state)
    print("1. Redirect the browser to:")
    print(f"   {auth_url}\n")
    print(f"   Store state={state!r} in the user's session.\n")

    # Step 2
    fake_callback = f"{REDIRECT_URI}?code=4f2e9a71bc44de&state={state}"
    print("2. GitHub calls back to:")
    print(f"   {fake_callback}\n")
    code = parse_callback(fake_callback, state)
    print(f"   State matched. Extracted code={code!r}\n")

    # CSRF demo
    print("   What happens with a tampered state:")
    try:
        parse_callback(f"{REDIRECT_URI}?code=evil&state=tampered", state)
    except ValueError as e:
        print(f"   ✗ {e}\n")

    # Step 3
    print("3. Exchange code for access token (server-to-server):")
    print(format_token_exchange(CLIENT_ID, CLIENT_SECRET, code, REDIRECT_URI))

    # Step 4
    print("\n4. Fetch the user's profile:")
    print(format_user_fetch("ghu_16C7e42F292c6912E7710c838347Ae178B4a"))

    print("\n5. Create your own session (see 03_session.py)")
    print("   Store user in DB, mint a JWT, set a cookie → normal auth from here.")


if __name__ == "__main__":
    main()
