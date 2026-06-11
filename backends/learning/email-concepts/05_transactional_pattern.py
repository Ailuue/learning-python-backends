"""
Concept 05 — The Transactional Email Pattern

In production you rarely send email directly via raw SMTP. Instead you use a
*transactional email service* (SendGrid, Postmark, Mailgun, AWS SES, Resend).

Why?
  Deliverability: services manage IP reputation, DKIM signing, bounce handling.
  Analytics: open rates, clicks, bounces, spam reports — all tracked for you.
  Scale: they handle retry queues, rate limits, and ISP relationships.
  APIs: you call an HTTP API instead of managing SMTP credentials everywhere.

The right architecture is an abstraction layer:
  - Define an `EmailSender` interface (protocol / abstract base)
  - Write concrete backends: `SmtpSender` (dev/test) and `SendGridSender` (prod)
  - Wire up the backend via environment config, not hardcoded in callers
  - Business logic (send_welcome, send_reset) calls the interface, not a backend

This is the same dependency-inversion pattern used for databases:
  app → Repository interface → { SQLite (test) | PostgreSQL (prod) }
  app → EmailSender interface → { SmtpSender (dev) | SendGridSender (prod) }

HOW TO RUN:
  docker compose up -d
  python 05_transactional_pattern.py
  Open http://localhost:8025 to see the email.
"""

import os
import json
import smtplib
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional


# ---------------------------------------------------------------------------
# Data model for an outbound email
# ---------------------------------------------------------------------------

@dataclass
class OutboundEmail:
    to:      str
    subject: str
    html:    str
    text:    str = ""
    from_name:    str = "My App"
    from_address: str = "app@example.com"
    reply_to:     Optional[str] = None
    tags:         list[str] = field(default_factory=list)   # for analytics grouping


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class EmailSender(ABC):
    @abstractmethod
    def send(self, email: OutboundEmail) -> dict:
        """Send the email. Returns a dict with at least {"id": "...", "status": "..."}."""


# ---------------------------------------------------------------------------
# Backend 1 — SMTP (used for local dev / integration tests)
# ---------------------------------------------------------------------------

class SmtpSender(EmailSender):

    def __init__(self, host: str = "localhost", port: int = 1025):
        self.host = host
        self.port = port

    def send(self, email: OutboundEmail) -> dict:
        msg = EmailMessage()
        msg["From"]    = formataddr((email.from_name, email.from_address))
        msg["To"]      = email.to
        msg["Subject"] = email.subject
        if email.reply_to:
            msg["Reply-To"] = email.reply_to
        msg.set_content(email.text or f"Please view this email in an HTML-capable client.\n\n{email.subject}")
        msg.add_alternative(email.html, subtype="html")

        with smtplib.SMTP(self.host, self.port) as smtp:
            smtp.send_message(msg)

        return {"id": f"smtp-local-{id(msg)}", "status": "sent"}


# ---------------------------------------------------------------------------
# Backend 2 — SendGrid HTTP API (used in production)
#
# To run this for real:
#   1. Create a free SendGrid account and generate an API key.
#   2. Set SENDGRID_API_KEY in your environment.
#   3. Replace the `simulate=True` default with `simulate=False`.
# ---------------------------------------------------------------------------

class SendGridSender(EmailSender):
    API_URL = "https://api.sendgrid.com/v3/mail/send"

    def __init__(self, api_key: str, simulate: bool = True):
        self._key = api_key
        self._simulate = simulate

    def send(self, email: OutboundEmail) -> dict:
        payload = {
            "personalizations": [{"to": [{"email": email.to}]}],
            "from": {"email": email.from_address, "name": email.from_name},
            "subject": email.subject,
            "content": [
                {"type": "text/plain", "value": email.text or email.subject},
                {"type": "text/html",  "value": email.html},
            ],
            "categories": email.tags,
        }
        if email.reply_to:
            payload["reply_to"] = {"email": email.reply_to}

        if self._simulate:
            print(f"   [SendGrid SIMULATED] POST {self.API_URL}")
            print(f"   payload keys: {list(payload.keys())}")
            return {"id": "sg-simulated-id-001", "status": "simulated"}

        # Real HTTP call
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.API_URL,
            data=data,
            headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return {"id": resp.headers.get("X-Message-Id", ""), "status": "sent"}
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"SendGrid error {e.code}: {body}") from e


# ---------------------------------------------------------------------------
# Business logic — calls the interface, not a backend
# ---------------------------------------------------------------------------

class EmailService:
    """
    Application-level email service. Uses whatever backend is injected.
    This is what your FastAPI endpoints / Celery tasks would call.
    """

    def __init__(self, sender: EmailSender):
        self._sender = sender

    def send_welcome(self, to: str, name: str, verify_token: str) -> dict:
        verify_url = f"https://myapp.example.com/verify?token={verify_token}"
        email = OutboundEmail(
            to=to,
            subject=f"Welcome to My App, {name}!",
            html=f"<h1>Hi {name}!</h1><p>Click <a href='{verify_url}'>here</a> to verify.</p>",
            text=f"Hi {name},\n\nVerify your account: {verify_url}\n",
            tags=["welcome", "onboarding"],
        )
        result = self._sender.send(email)
        print(f"   send_welcome → {result}")
        return result

    def send_password_reset(self, to: str, name: str, token: str) -> dict:
        reset_url = f"https://myapp.example.com/reset?token={token}"
        email = OutboundEmail(
            to=to,
            subject="Reset your password",
            html=f"<p>Hi {name}, <a href='{reset_url}'>reset your password</a>.</p>",
            text=f"Hi {name},\n\nReset your password: {reset_url}\n",
            reply_to="support@myapp.example.com",
            tags=["password-reset", "transactional"],
        )
        result = self._sender.send(email)
        print(f"   send_password_reset → {result}")
        return result


# ---------------------------------------------------------------------------
# Factory — choose backend from environment
# ---------------------------------------------------------------------------

def make_email_service() -> EmailService:
    """
    Create the right backend based on the environment.
    In dev/test: no env var → use Mailpit over SMTP.
    In production: set SENDGRID_API_KEY → use SendGrid.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    if api_key:
        print("   Using SendGridSender (SENDGRID_API_KEY is set)")
        sender = SendGridSender(api_key=api_key, simulate=False)
    else:
        print("   Using SmtpSender → Mailpit (no SENDGRID_API_KEY in env)")
        sender = SmtpSender(host="localhost", port=1025)
    return EmailService(sender)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 05 — Transactional Email Pattern")
    print("=" * 60)

    # ── Dev/test: SMTP backend → Mailpit ──────────────────────────────────
    print("\n1. Dev mode (SmtpSender → Mailpit):")
    dev_service = EmailService(SmtpSender())
    dev_service.send_welcome("alex@example.com", "Alex", "tok_verify_abc")
    dev_service.send_password_reset("alex@example.com", "Alex", "tok_reset_xyz")

    # ── Production-like: SendGrid backend (simulated, no real API call) ───
    print("\n2. Production mode (SendGridSender, simulate=True — no real API call):")
    prod_service = EmailService(SendGridSender(api_key="fake-key", simulate=True))
    prod_service.send_welcome("dana@example.com", "Dana", "tok_verify_def")

    # ── Factory pattern ───────────────────────────────────────────────────
    print("\n3. Factory (auto-detects from environment):")
    service = make_email_service()
    service.send_welcome("user@example.com", "User", "tok_factory_ghi")

    print("\nCheck http://localhost:8025 for messages sent via SmtpSender.")


if __name__ == "__main__":
    main()
