"""
03_signing.py — Webhook Signature Verification

Anyone who knows your webhook URL can POST fake events to it.
Signature verification proves the event actually came from the sender.

How it works (Stripe-style):
  Sender:   computes HMAC-SHA256(secret, "{timestamp}.{body}")
            sends X-Webhook-Signature and X-Webhook-Timestamp headers

  Receiver: recomputes the same HMAC using the shared secret
            rejects if signatures don't match  → payload was tampered
            rejects if timestamp is >5 min old → replay attack

The shared secret is generated once and stored on both sides.
It is never sent as part of any request.

Run:
    python 03_signing.py
"""

import hashlib
import hmac
import json
import time


SECRET = "shared-webhook-secret-never-send-this-in-a-request"
TOLERANCE_SECONDS = 300  # reject events older than 5 minutes


# ── Sender side ────────────────────────────────────────────────────────────────

def sign(body: bytes, timestamp: int, secret: str) -> str:
    """Compute HMAC-SHA256 over '{timestamp}.{body}'."""
    msg = f"{timestamp}.".encode() + body
    return hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()


def build_signed_headers(body: bytes, secret: str) -> dict:
    ts = int(time.time())
    return {
        "Content-Type": "application/json",
        "X-Webhook-Timestamp": str(ts),
        "X-Webhook-Signature": sign(body, ts, secret),
    }


# ── Receiver side ──────────────────────────────────────────────────────────────

def verify(body: bytes, timestamp: int, received_sig: str, secret: str) -> None:
    """Raises ValueError if the signature is invalid or the event is stale."""
    age = abs(time.time() - timestamp)
    if age > TOLERANCE_SECONDS:
        raise ValueError(f"Event is {age:.0f}s old — possible replay attack")

    expected = sign(body, timestamp, secret)

    # compare_digest does constant-time comparison to prevent timing attacks.
    # A plain == leaks information about where strings first differ.
    if not hmac.compare_digest(expected, received_sig):
        raise ValueError("Signature mismatch — payload may have been tampered")


# ── Demonstration ──────────────────────────────────────────────────────────────

def demo():
    payload = {"event": "payment.succeeded", "id": "evt_abc123", "data": {"amount": 4999}}
    body = json.dumps(payload).encode()
    headers = build_signed_headers(body, SECRET)
    ts = int(headers["X-Webhook-Timestamp"])
    sig = headers["X-Webhook-Signature"]

    print("=== Sender ===")
    print(f"  Timestamp : {ts}")
    print(f"  Signature : {sig[:32]}…")

    print("\n=== Receiver: valid event ===")
    try:
        verify(body, ts, sig, SECRET)
        print("  OK — signature verified")
    except ValueError as e:
        print(f"  REJECTED — {e}")

    print("\n=== Receiver: tampered payload (amount changed to 0) ===")
    tampered = json.dumps({**payload, "data": {"amount": 0}}).encode()
    try:
        verify(tampered, ts, sig, SECRET)
        print("  OK — signature verified")
    except ValueError as e:
        print(f"  REJECTED — {e}")

    print("\n=== Receiver: replay attack (timestamp 10 minutes old) ===")
    old_ts = int(time.time()) - 600
    old_sig = sign(body, old_ts, SECRET)  # was a valid sig when sent
    try:
        verify(body, old_ts, old_sig, SECRET)
        print("  OK — signature verified")
    except ValueError as e:
        print(f"  REJECTED — {e}")

    print("\n=== Receiver: wrong secret (attacker doesn't have it) ===")
    attacker_sig = sign(body, ts, "wrong-secret")
    try:
        verify(body, ts, attacker_sig, SECRET)
        print("  OK — signature verified")
    except ValueError as e:
        print(f"  REJECTED — {e}")


if __name__ == "__main__":
    demo()
