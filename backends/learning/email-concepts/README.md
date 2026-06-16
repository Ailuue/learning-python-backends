# Email Concepts

> 📚 [Backend Learning](../README.md) · **Specialized topic** — best after the core path.

Sending, building, templating, testing, and reading email from Python.

## The email stack in one picture

```
Your code
   │
   │ smtplib (stdlib)           → submits outbound email
   ▼
SMTP server (Mailpit locally, SendGrid/SES in prod)
   │
   │ delivers to recipient's server
   ▼
Recipient's mailbox
   │
   │ imaplib (stdlib)           → reads inbound email
   ▼
Your code
```

Mailpit is a local mail catcher. Every email your code sends to port 1025 is
captured and shown in a web UI at http://localhost:8025. Nothing actually gets
delivered to a real inbox — perfect for development.

## Setup

```bash
pip install -r requirements.txt     # just jinja2; smtplib + imaplib are stdlib
docker compose up -d                 # starts Mailpit
```

Open http://localhost:8025 after running any file to inspect captured emails.

## Concept files

| File | What you'll learn |
|------|-------------------|
| [01_smtp_basics.py](01_smtp_basics.py) | SMTP connection modes (plain, STARTTLS, SSL), `send_message` vs `sendmail`, debug logging |
| [02_message_building.py](02_message_building.py) | `EmailMessage`, HTML + plain fallback, attachments, CC/BCC, custom headers |
| [03_templates.py](03_templates.py) | Jinja2 `Environment`, template inheritance, auto-escaping, sending rendered emails |
| [04_testing.py](04_testing.py) | `unittest.mock.patch` for SMTP, Mailpit HTTP API for integration assertions |
| [05_transactional_pattern.py](05_transactional_pattern.py) | `EmailSender` abstraction, SMTP backend (dev) vs HTTP API backend (prod), factory |
| [06_imap_reading.py](06_imap_reading.py) | IMAP login, SELECT, SEARCH, FETCH, parse bodies, mark as read |

## Running each file

```bash
docker compose up -d
python 01_smtp_basics.py
# open http://localhost:8025 after each run
```

Files 01–03 and 05–06 require Mailpit running.
File 04 has unit tests that run without any server, plus integration tests that need Mailpit.

## Templates

```
templates/
  base.html           ← shared header / footer layout
  welcome.html        ← extends base — new user verification email
  password_reset.html ← extends base — password reset link
```

Add new email types by creating a new `.html` file that `{% extends "base.html" %}`.

## Key concepts at a glance

### Three SMTP connection modes
```python
# Plain (local dev only — never over the internet)
smtplib.SMTP("localhost", 1025)

# STARTTLS (standard port 587, upgrade mid-connection)
smtp = smtplib.SMTP("smtp.gmail.com", 587)
smtp.starttls(context=ssl.create_default_context())
smtp.login("user", "app-password")

# SMTP_SSL (port 465, TLS from the start — preferred)
smtplib.SMTP_SSL("smtp.example.com", 465, context=ssl.create_default_context())
```

### Message structure
```python
from email.message import EmailMessage
msg = EmailMessage()
msg["From"]    = "app@example.com"
msg["To"]      = "user@example.com"
msg["Subject"] = "Hello"
msg.set_content("Plain text fallback")
msg.add_alternative("<h1>HTML body</h1>", subtype="html")
msg.add_attachment(bytes_data, maintype="application", subtype="octet-stream", filename="file.pdf")
```

### MIME structure for HTML + attachment
```
multipart/mixed
  multipart/alternative
    text/plain      ← client shows this if it can't render HTML
    text/html       ← client shows this if it can render HTML
  application/octet-stream   ← attachment
```

### EmailSender abstraction
```python
class EmailSender(ABC):
    @abstractmethod
    def send(self, email: OutboundEmail) -> dict: ...

# Inject the right backend based on environment:
sender = SmtpSender()          # dev  → Mailpit
sender = SendGridSender(key)   # prod → real delivery
service = EmailService(sender)
service.send_welcome("user@example.com", "Alex", token)
```

### IMAP quick reference
```python
mail = imaplib.IMAP4("localhost", 1143)
mail.login("user", "pass")
mail.select("INBOX")

ok, ids  = mail.search(None, "ALL")           # all messages
ok, ids  = mail.search(None, "UNSEEN")        # unread only
ok, ids  = mail.search(None, 'SUBJECT "x"')  # subject filter
ok, ids  = mail.search(None, 'FROM "x@y"')   # sender filter

ok, data = mail.fetch(msg_id, "(RFC822)")     # full message
msg      = email.message_from_bytes(data[0][1])

mail.store(msg_id, "+FLAGS", r"\Seen")        # mark as read
mail.store(msg_id, "+FLAGS", r"\Deleted")     # mark for deletion
mail.expunge()                                 # permanently delete flagged
```

### Testing patterns
```python
# Unit: mock SMTP so no connection is made
@patch("smtplib.SMTP")
def test_sends(self, MockSMTP):
    send_welcome_email(...)
    MockSMTP.return_value.__enter__.return_value.send_message.assert_called_once()

# Integration: send to Mailpit, query its API
import urllib.request, json
data = json.loads(urllib.request.urlopen("http://localhost:8025/api/v1/messages").read())
assert data["messages"][0]["Subject"] == "Welcome!"
```

## Deliverability note (production)

When you move from Mailpit to real delivery, three DNS records protect your domain:
- **SPF** — lists which IP addresses are allowed to send for your domain
- **DKIM** — cryptographic signature on every outbound message (transactional services set this up for you)
- **DMARC** — policy for what happens when SPF/DKIM fail (reject, quarantine, report)

Transactional services (SendGrid, Postmark, Mailgun) handle SPF/DKIM setup for you. Raw SMTP from your own server requires configuring all three manually.
