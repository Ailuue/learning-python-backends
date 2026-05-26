import os
import pwd

from fastapi import FastAPI

app = FastAPI(title="Docker Security Practice")


def read_secret(name: str) -> str | None:
    """
    Read a Docker secret mounted at /run/secrets/<name>.
    This is how secrets: in docker-compose.yml surface inside the container.
    The value is never in an env var — not visible in docker inspect.
    """
    try:
        with open(f"/run/secrets/{name}") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


@app.get("/")
def root():
    return {"message": "Docker Security Practice", "env": os.environ.get("APP_ENV", "unknown")}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/whoami")
def whoami():
    """
    Proves the container is running as non-root.
    curl this on the secure image vs the insecure image and compare:
      Secure:   {"uid": 1001, "username": "appuser", "is_root": false}
      Insecure: {"uid": 0,    "username": "root",    "is_root": true}
    """
    uid = os.getuid()
    try:
        username = pwd.getpwuid(uid).pw_name
    except KeyError:
        username = f"uid:{uid}"
    return {"uid": uid, "username": username, "is_root": uid == 0}


@app.get("/secrets/check")
def check_secrets():
    """
    Verifies the secret is accessible via /run/secrets/ but NOT via env vars.
    Never return secret values from a real API — this just checks presence.
    """
    secret = read_secret("app_secret_key")
    return {
        "secret_mounted": secret is not None,
        "secret_in_env": "APP_SECRET_KEY" in os.environ,  # should always be False
        "secret_length": len(secret) if secret else 0,
    }
