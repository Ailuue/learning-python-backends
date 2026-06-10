# JWT & RBAC

## What is this?

**JWT (JSON Web Token)** is a compact, signed token a server issues after login. The client sends it with every subsequent request. The server verifies the signature and trusts the claims inside — no database lookup, no session store.

**RBAC (Role-Based Access Control)** is the pattern of attaching a role to the user's identity (in the JWT claims) and enforcing it at the route level. Every route specifies the minimum role required; users below that level get 403 Forbidden.

Together they form the most common auth pattern in modern backends.

## The two questions auth answers

| Question | Term | HTTP code on failure |
|---|---|---|
| Who are you? | Authentication | 401 Unauthorized |
| What can you do? | Authorization | 403 Forbidden |

It's important not to conflate these. A valid token that lacks permission is a 403, not a 401.

## What the files cover

| File | What it teaches |
|---|---|
| `01_jwt_basics.py` | JWT structure, tampering detection, expiry — pure script, no server |
| `02_auth_flow.py` | Login endpoint, token issuance, protected routes via `Depends()` |
| `03_rbac.py` | Role hierarchy, dependency factory `require_role()`, 401 vs 403 |
| `04_refresh_tokens.py` | Short-lived access + long-lived refresh, token rotation, logout/revocation |

## How to run

```bash
pip install -r requirements.txt
```

**File 01 — JWT internals (no server needed)**
```bash
python 01_jwt_basics.py
```

**File 02 — auth flow**
```bash
uvicorn 02_auth_flow:app --port 8000 --reload

# Login
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}' | python -m json.tool

# Access a protected route
curl http://localhost:8000/me -H "Authorization: Bearer <token>"
```

**File 03 — RBAC**
```bash
uvicorn 03_rbac:app --port 8000 --reload

# Get tokens for each role
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" -d '{"username": "alice", "password": "secret"}' \
  | python -m json.tool   # admin

curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" -d '{"username": "bob", "password": "hunter2"}' \
  | python -m json.tool   # editor

curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" -d '{"username": "carol", "password": "pass"}' \
  | python -m json.tool   # viewer

# Try routes with different roles — watch the 403s
curl    http://localhost:8000/articles              -H "Authorization: Bearer <viewer>"
curl -X POST http://localhost:8000/articles         -H "Authorization: Bearer <viewer>"   # → 403
curl -X DELETE http://localhost:8000/articles/1     -H "Authorization: Bearer <editor>"   # → 403
curl -X DELETE http://localhost:8000/articles/1     -H "Authorization: Bearer <admin>"    # → 200
```

**File 04 — refresh tokens**
```bash
uvicorn 04_refresh_tokens:app --port 8000 --reload

# Login — you'll get both tokens
curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}' | python -m json.tool

# Use access_token for API calls
curl http://localhost:8000/me -H "Authorization: Bearer <access_token>"

# Get a new pair using the refresh_token
curl -s -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}' | python -m json.tool

# Old refresh_token is now dead (token rotation)
curl -s -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<old_refresh_token>"}' | python -m json.tool  # → 401

# Logout revokes the refresh token
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## Key concepts

**JWTs are signed, not encrypted.** Anyone can base64-decode the payload and read the claims. The signature only proves it hasn't been tampered with. Never put secrets or passwords in a JWT.

**Stateless verification.** The server verifies a JWT using only its own secret key — no database, no Redis, no shared state. This is the main performance benefit of JWTs over session tokens.

**The `Depends()` factory pattern.** `require_role("admin")` returns a FastAPI dependency function. This lets you write the authorization logic once and compose it onto any route. It's the same pattern as `get_current_user` but parameterized.

**Access + refresh token split.** Short-lived access tokens limit blast radius if stolen. Long-lived refresh tokens need to be stored server-side so they can be revoked on logout. Access tokens can't be revoked — they just expire.

**Token rotation.** On every refresh, invalidate the old refresh token and issue a new one. If an attacker steals a refresh token and uses it, the legitimate client's next refresh will fail (the JTI is gone), revealing the compromise.

**`hmac.compare_digest` vs `==`.** PyJWT does this for you internally, but it's worth knowing: comparing tokens with `==` leaks timing information that can reveal how many bytes match. `compare_digest` takes constant time regardless of where the strings first differ.
