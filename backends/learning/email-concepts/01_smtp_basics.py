"""
Concept 01 — SMTP Basics

SMTP (Simple Mail Transfer Protocol) is the protocol your code uses to *submit*
an email to a mail server, which then delivers it to the recipient.

                  your code
                     │
              smtplib.SMTP / SMTP_SSL
                     │
             ┌───────▼────────┐
             │  SMTP server   │  ← Mailpit locally, Gmail/SendGrid in prod
             └───────┬────────┘
                     │
             ┌───────▼────────┐
             │  Recipient's   │
             │  mail server   │
             └────────────────┘

Three connection modes (ordered from worst to best security):
  SMTP(host, 25)              Plain text — never use in production
  SMTP(host, 587) + starttls  Starts plain, upgrades to TLS mid-connection
  SMTP_SSL(host, 465)         TLS from the very first byte (preferred)

Mailpit runs on port 1025 and accepts plain-text connections — ideal for
local dev because you don't need certs or real credentials.

HOW TO RUN:
  docker compose up -d
  python 01_smtp_basics.py
  Open http://localhost:8025 to see the email in Mailpit's web UI.
"""

import smtplib
import ssl
from email.message import EmailMessage

SMTP_HOST = "localhost"
SMTP_PORT = 1025          # Mailpit
FROM_ADDR = "app@example.com"
TO_ADDR   = "alex@example.com"


# ---------------------------------------------------------------------------
# Helper — build the simplest possible message
# ---------------------------------------------------------------------------

def make_message(subject: str, body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["From"]    = FROM_ADDR
    msg["To"]      = TO_ADDR
    msg["Subject"] = subject
    msg.set_content(body)
    return msg


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 01 — SMTP Basics")
    print("=" * 60)

    # ── 1. Plain SMTP (no TLS) ────────────────────────────────────────────
    # This is what Mailpit accepts locally.
    # In production you would NEVER use a plain connection over the internet.
    print("\n1. Plain SMTP connection (Mailpit on port 1025):")
    msg = make_message("Test 1 — Plain SMTP", "Hello from plain SMTP!")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        print(f"   Connected to {SMTP_HOST}:{SMTP_PORT}")
        print(f"   EHLO response: {smtp.ehlo()[1][:60]}...")
        smtp.send_message(msg)
        print("   Message sent. Check http://localhost:8025")

    # ── 2. SMTP with STARTTLS ─────────────────────────────────────────────
    # Port 587 is the standard "submission" port. You start plain, then call
    # starttls() to upgrade. Most cloud SMTP providers (Gmail, SendGrid) use this.
    # Mailpit doesn't require TLS so we skip actual starttls() here — just show
    # the pattern you'd use against a real server.
    print("\n2. SMTP + STARTTLS pattern (shown, not run against Mailpit):")
    print("""
   context = ssl.create_default_context()
   with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
       smtp.ehlo()
       smtp.starttls(context=context)   # upgrade to TLS here
       smtp.ehlo()                       # re-identify after TLS
       smtp.login("you@gmail.com", "app-password")
       smtp.send_message(msg)
    """)

    # ── 3. SMTP_SSL (TLS from the start) ─────────────────────────────────
    # Port 465 (SMTPS) — TLS wraps the entire connection, no upgrade needed.
    print("3. SMTP_SSL pattern (shown, not run against Mailpit):")
    print("""
   context = ssl.create_default_context()
   with smtplib.SMTP_SSL("smtp.example.com", 465, context=context) as smtp:
       smtp.login("user@example.com", "password")
       smtp.send_message(msg)
    """)

    # ── 4. Inspecting the SMTP conversation ──────────────────────────────
    # set_debuglevel(1) prints every SMTP command and response — useful when
    # debugging delivery issues.
    print("4. SMTP debug output (level=1):")
    msg2 = make_message("Test 2 — Debug mode", "Watching SMTP commands fly by.")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.set_debuglevel(1)
        smtp.send_message(msg2)

    # ── 5. send_message vs sendmail ───────────────────────────────────────
    # send_message(EmailMessage) — modern, handles encoding automatically.
    # sendmail(from, to, raw_string) — low-level, you manage the raw bytes.
    # Always prefer send_message unless you have a specific reason not to.
    print("\n5. Two send APIs:")
    print("   send_message(msg)          — takes an EmailMessage object (use this)")
    print("   sendmail(from, [to], data) — takes raw RFC 2822 bytes (low-level)")

    print("\nAll done. Open http://localhost:8025 to see the two messages Mailpit captured.")


if __name__ == "__main__":
    main()
