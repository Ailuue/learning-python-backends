"""
01_jwt_basics.py — What a JWT Actually Is
==========================================
A JWT is three base64url-encoded JSON blobs joined with dots:

    HEADER.PAYLOAD.SIGNATURE

    Header     → {"alg": "HS256", "typ": "JWT"}
    Payload    → {"sub": "user_42", "role": "admin", "exp": 1718000000}
    Signature  → HMAC-SHA256(base64url(header) + "." + base64url(payload), secret)

The header and payload are encoded, NOT encrypted.
Anyone can read them — they just can't fake the signature without the secret.
Never put passwords or sensitive secrets in a JWT payload.

The signature guarantees integrity: if anyone changes even one byte of the
header or payload, the signature will no longer match.

Standard claims (IANA-registered):
    sub   subject — who the token is for (usually a user ID)
    iat   issued at — Unix timestamp when the token was minted
    exp   expiry — Unix timestamp after which the token is invalid
    jti   JWT ID — a unique identifier for this specific token

Run:
    python 01_jwt_basics.py
"""

import base64
import json
import time

import jwt  # PyJWT

SECRET = "dev-secret-key-minimum-32-bytes!!"  # HS256 requires ≥32 bytes


def decode_part(b64: str) -> dict:
    """Decode a single base64url-encoded JWT part without verifying."""
    padded = b64 + "=" * (-len(b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def main():
    # ── Encode a token ─────────────────────────────────────────────────────────

    now = int(time.time())
    payload = {
        "sub": "user_42",
        "name": "Alex",
        "role": "admin",
        "iat": now,
        "exp": now + 3600,
    }

    token = jwt.encode(payload, SECRET, algorithm="HS256")

    print("=== Encoded token ===")
    print(token)

    # ── Inspect without the secret — shows it's just base64 ───────────────────

    print("\n=== Decode the parts manually (no secret needed) ===")
    header_b64, payload_b64, sig_b64 = token.split(".")
    print(f"  Header  : {decode_part(header_b64)}")
    print(f"  Payload : {decode_part(payload_b64)}")
    print(f"  Sig     : {sig_b64[:20]}…  (can't forge this without the secret)")

    # ── Verify a valid token ───────────────────────────────────────────────────

    print("\n=== Verify a valid token ===")
    decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
    print(f"  OK: {decoded}")

    # ── Tampered payload ───────────────────────────────────────────────────────

    print("\n=== Tampered payload (role changed to 'superadmin') ===")
    evil_payload = {**payload, "role": "superadmin"}
    evil_b64 = (
        base64.urlsafe_b64encode(json.dumps(evil_payload).encode())
        .rstrip(b"=")
        .decode()
    )
    tampered_token = f"{header_b64}.{evil_b64}.{sig_b64}"
    try:
        jwt.decode(tampered_token, SECRET, algorithms=["HS256"])
        print("  Verified (should never happen)")
    except jwt.InvalidSignatureError as e:
        print(f"  REJECTED — {e}")

    # ── Expired token ──────────────────────────────────────────────────────────

    print("\n=== Expired token ===")
    expired = jwt.encode({**payload, "exp": now - 10}, SECRET, algorithm="HS256")
    try:
        jwt.decode(expired, SECRET, algorithms=["HS256"])
        print("  Verified (should never happen)")
    except jwt.ExpiredSignatureError as e:
        print(f"  REJECTED — {e}")

    # ── Wrong secret ───────────────────────────────────────────────────────────

    print("\n=== Valid token verified with wrong secret ===")
    try:
        jwt.decode(token, "wrong-secret-key-minimum-32-bytes!!", algorithms=["HS256"])
        print("  Verified (should never happen)")
    except jwt.InvalidSignatureError as e:
        print(f"  REJECTED — {e}")


if __name__ == "__main__":
    main()
