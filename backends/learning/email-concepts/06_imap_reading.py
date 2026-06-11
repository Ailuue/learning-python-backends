"""
Concept 06 — Reading Email with IMAP

IMAP (Internet Message Access Protocol) lets your code *read* email from a
mailbox — the receiving side of the email stack.

Common backend use cases:
  - Support inbox automation: parse incoming tickets, auto-assign
  - Email-to-action pipelines: parse "reply to unsubscribe" emails
  - Processing email receipts (invoice parsing, delivery confirmations)
  - Polling for replies to transactional emails

We use Mailpit's built-in IMAP server (port 1143) so we can send test emails
and immediately read them back in the same session.

IMAP protocol flow:
  1. Connect  →  IMAP4 / IMAP4_SSL
  2. Login    →  LOGIN user password
  3. Select   →  SELECT INBOX   (makes a mailbox active)
  4. Search   →  SEARCH criteria  → list of message IDs
  5. Fetch    →  FETCH id (RFC822)  → raw message bytes
  6. Parse    →  email.message_from_bytes()
  7. Logout   →  LOGOUT

Search criteria examples (passed as a string to mail.search()):
  ALL           every message in the mailbox
  UNSEEN        unread messages
  FROM "x"      messages from a given address
  SUBJECT "y"   subject contains y
  SINCE DD-Mon-YYYY   messages after a date

HOW TO RUN:
  docker compose up -d
  python 06_imap_reading.py
"""

import email
import imaplib
import smtplib
import time
from email.message import EmailMessage


SMTP_HOST  = "localhost"
SMTP_PORT  = 1025
IMAP_HOST  = "localhost"
IMAP_PORT  = 1143
# Mailpit accepts any credentials over IMAP when auth-accept-any is enabled
IMAP_USER  = "any"
IMAP_PASS  = "any"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def send_test_email(to: str, subject: str, body: str, html: str = ""):
    """Send an email to Mailpit so we have something to read back."""
    msg = EmailMessage()
    msg["From"]    = "sender@example.com"
    msg["To"]      = to
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(msg)


def parse_message(raw: bytes) -> email.message.Message:
    return email.message_from_bytes(raw)


def get_body(msg: email.message.Message) -> dict:
    """Extract plain-text and HTML body from a parsed message."""
    plain, html = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain" and not plain:
                plain = part.get_payload(decode=True).decode(errors="replace")
            elif ct == "text/html" and not html:
                html = part.get_payload(decode=True).decode(errors="replace")
    else:
        plain = msg.get_payload(decode=True).decode(errors="replace")
    return {"plain": plain.strip(), "html": html.strip()}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 06 — Reading Email with IMAP")
    print("=" * 60)

    # Seed Mailpit with a few test messages to read back
    print("\nSeeding Mailpit with test emails...")
    send_test_email("inbox@example.com", "Invoice #1001",
                    "Your invoice for $99.00 is attached.", "<p>Invoice <b>$99.00</b></p>")
    send_test_email("inbox@example.com", "Support request: login broken",
                    "Hi, I can't log in. Please help.", "")
    send_test_email("inbox@example.com", "Invoice #1002",
                    "Your invoice for $149.00 is ready.", "<p>Invoice <b>$149.00</b></p>")
    send_test_email("other@example.com", "Unrelated email",
                    "This one goes to a different address.", "")
    time.sleep(0.3)  # let Mailpit index the messages

    # ── Connect and login ─────────────────────────────────────────────────
    print("\n1. Connect and login to IMAP:")
    mail = imaplib.IMAP4(IMAP_HOST, IMAP_PORT)
    ok, caps = mail.login(IMAP_USER, IMAP_PASS)
    print(f"   Login: {ok}")

    # ── List available mailboxes ──────────────────────────────────────────
    print("\n2. List mailboxes:")
    ok, mailboxes = mail.list()
    for mb in mailboxes:
        print(f"   {mb.decode()}")

    # ── Select INBOX and search ALL ───────────────────────────────────────
    print("\n3. Select INBOX, fetch all message IDs:")
    ok, data = mail.select("INBOX")
    print(f"   Messages in INBOX: {data[0].decode()}")

    ok, msg_ids = mail.search(None, "ALL")
    ids = msg_ids[0].split()   # list of b"1", b"2", ...
    print(f"   IDs: {[i.decode() for i in ids]}")

    # ── Fetch and print each message ─────────────────────────────────────
    print("\n4. Fetch and parse each message:")
    for msg_id in ids:
        ok, raw_data = mail.fetch(msg_id, "(RFC822)")
        raw_bytes = raw_data[0][1]
        msg = parse_message(raw_bytes)
        body = get_body(msg)
        print(f"\n   ID={msg_id.decode()}")
        print(f"   From:    {msg['From']}")
        print(f"   To:      {msg['To']}")
        print(f"   Subject: {msg['Subject']}")
        print(f"   Body:    {body['plain'][:60]!r}{'...' if len(body['plain']) > 60 else ''}")
        if body["html"]:
            print(f"   HTML:    {body['html'][:60]!r}...")

    # ── Search by subject keyword ─────────────────────────────────────────
    print("\n5. Search SUBJECT containing 'Invoice':")
    ok, inv_ids = mail.search(None, 'SUBJECT "Invoice"')
    ids = inv_ids[0].split()
    print(f"   Found {len(ids)} invoice message(s): IDs {[i.decode() for i in ids]}")

    # ── Mark a message as read (set \Seen flag) ───────────────────────────
    if ids:
        first_id = ids[0]
        print(f"\n6. Mark message {first_id.decode()} as read:")
        mail.store(first_id, "+FLAGS", r"\Seen")

        # Verify: search for UNSEEN — the marked message should no longer appear
        ok, unseen_ids = mail.search(None, "UNSEEN")
        unseen = unseen_ids[0].split()
        print(f"   Unseen IDs after marking: {[i.decode() for i in unseen]}")
        print(f"   (message {first_id.decode()} is gone from UNSEEN list)")

    # ── Peek at headers only (no body) — useful for bulk triage ──────────
    print("\n7. Fetch only headers (BODY.PEEK[HEADER]) for all messages:")
    ok, header_data = mail.fetch("1:*", "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
    for item in header_data:
        if isinstance(item, tuple):
            headers = email.message_from_bytes(item[1])
            print(f"   {headers['Date'] or '?'} | {headers['From']} | {headers['Subject']}")

    mail.close()
    mail.logout()
    print("\nDone. IMAP session closed.")


if __name__ == "__main__":
    main()
