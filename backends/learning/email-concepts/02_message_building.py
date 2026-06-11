"""
Concept 02 — Message Building

An email message is structured as MIME (Multipurpose Internet Mail Extensions).
MIME allows a single email to carry multiple representations and attachments,
nested in a tree of "parts".

Common MIME structures:

  Plain text only:
    text/plain

  HTML with a plain-text fallback (most emails work this way):
    multipart/alternative
      text/plain     ← shown by clients that don't render HTML
      text/html      ← shown by clients that do

  HTML + attachment:
    multipart/mixed
      multipart/alternative
        text/plain
        text/html
      application/octet-stream  ← the attachment

Python's `email.message.EmailMessage` (stdlib, 3.6+) builds this tree for you.
You rarely touch the MIME structure directly.

HOW TO RUN:
  docker compose up -d
  python 02_message_building.py
  Open http://localhost:8025 — you should see four messages.
"""

import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

SMTP_HOST = "localhost"
SMTP_PORT = 1025
FROM_ADDR = "app@example.com"
FROM_NAME = "My App"


def send(msg: EmailMessage):
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(msg)
    print(f"   Sent: {msg['Subject']!r}")


def main():
    print("=" * 60)
    print("CONCEPT 02 — Message Building")
    print("=" * 60)

    # ── 1. Plain text ──────────────────────────────────────────────────────
    print("\n1. Plain text message:")
    msg1 = EmailMessage()
    msg1["From"]    = formataddr((FROM_NAME, FROM_ADDR))   # "My App <app@example.com>"
    msg1["To"]      = "alex@example.com"
    msg1["Subject"] = "Test 1 — Plain text"
    msg1.set_content("Hello Alex,\n\nThis is a plain text email.\n\n— My App")
    send(msg1)

    # ── 2. HTML + plain-text fallback ────────────────────────────────────
    # add_alternative() adds a second part under multipart/alternative.
    # The *last* alternative wins in most clients (RFC 2046 §5.1.4),
    # so put HTML last.
    print("\n2. HTML + plain-text fallback (multipart/alternative):")
    msg2 = EmailMessage()
    msg2["From"]    = formataddr((FROM_NAME, FROM_ADDR))
    msg2["To"]      = "alex@example.com"
    msg2["Subject"] = "Test 2 — HTML email"
    msg2.set_content("Hello Alex,\n\nThis is the plain text fallback.")
    msg2.add_alternative("""\
<html>
  <body>
    <h2>Hello Alex,</h2>
    <p>This is an <strong>HTML</strong> email with a plain-text fallback.</p>
    <p>If you're reading this, your client renders HTML.</p>
  </body>
</html>
""", subtype="html")
    send(msg2)

    # ── 3. Multiple recipients, CC, BCC, Reply-To ─────────────────────────
    # BCC recipients aren't visible in the message headers — smtplib handles
    # delivery separately. You pass them in the envelope, not the header.
    print("\n3. Multiple To, CC, BCC, Reply-To:")
    msg3 = EmailMessage()
    msg3["From"]     = formataddr((FROM_NAME, FROM_ADDR))
    msg3["To"]       = "alex@example.com, dana@example.com"
    msg3["Cc"]       = "boss@example.com"
    msg3["Reply-To"] = "support@example.com"
    msg3["Subject"]  = "Test 3 — Multiple recipients"
    # X-headers are custom headers — widely used for tracking and metadata
    msg3["X-Campaign-ID"] = "welcome-series-01"
    msg3.set_content("This goes to Alex and Dana, CC's the boss.")

    # For BCC: pass all recipients to sendmail/send_message, but don't put
    # BCC addresses in the header. smtplib accepts a list of envelope recipients.
    bcc = ["secret@example.com"]
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(msg3, to_addrs=["alex@example.com", "dana@example.com"] + bcc)
    print(f"   Sent: {msg3['Subject']!r}")

    # ── 4. File attachment ────────────────────────────────────────────────
    print("\n4. Email with a file attachment:")
    msg4 = EmailMessage()
    msg4["From"]    = formataddr((FROM_NAME, FROM_ADDR))
    msg4["To"]      = "alex@example.com"
    msg4["Subject"] = "Test 4 — Attachment"
    msg4.set_content("Please find the report attached.")
    msg4.add_alternative("""\
<html><body>
  <p>Please find the report attached.</p>
</body></html>
""", subtype="html")

    # Create a dummy file to attach
    csv_data = b"name,score\nAlex,95\nDana,88\nJordan,72\n"
    msg4.add_attachment(
        csv_data,
        maintype="text",
        subtype="csv",
        filename="report.csv",
    )

    # A binary attachment (PDF-like)
    fake_pdf = b"%PDF-1.4 fake content for demo"
    msg4.add_attachment(
        fake_pdf,
        maintype="application",
        subtype="octet-stream",   # generic binary
        filename="report.pdf",
    )
    send(msg4)

    print("\nAll done. Open http://localhost:8025 to inspect all four messages.")
    print("Notice in message 4: Mailpit shows the HTML body and lets you download both attachments.")


if __name__ == "__main__":
    main()
