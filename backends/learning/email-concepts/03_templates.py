"""
Concept 03 — Email Templates with Jinja2

Hardcoding HTML inside Python strings doesn't scale. Jinja2 templates let you:
  - Keep HTML in .html files, edited independently of Python code
  - Use template inheritance (base layout + per-email overrides)
  - Inject dynamic data safely (auto-escaping prevents HTML injection)
  - Reuse partial snippets across emails

Template files live in templates/:
  base.html           — shared header/footer/styles layout
  welcome.html        — new user onboarding (extends base)
  password_reset.html — password reset link (extends base)

Jinja2's {% extends %} and {% block %} work exactly like Django/Flask templates.

One important production caveat: most email clients (especially Outlook) don't
support CSS classes or <style> blocks — only inline styles (style="...").
Tooling like `premailer` automatically inlines CSS before sending.
This demo keeps styles in a <style> block for readability; noted in the code.

HOW TO RUN:
  pip install -r requirements.txt
  docker compose up -d
  python 03_templates.py
  Open http://localhost:8025 to see the rendered emails.
"""

import smtplib
from datetime import datetime
from pathlib import Path

from email.message import EmailMessage
from email.utils import formataddr

from jinja2 import Environment, FileSystemLoader, select_autoescape

SMTP_HOST   = "localhost"
SMTP_PORT   = 1025
FROM_ADDR   = "app@example.com"
FROM_NAME   = "My App"
TEMPLATES   = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Template engine setup
# ---------------------------------------------------------------------------

env = Environment(
    loader=FileSystemLoader(TEMPLATES),
    autoescape=select_autoescape(["html"]),  # auto-escape HTML entities
)

# Inject globals available in every template without passing them explicitly
env.globals["year"] = datetime.now().year


# ---------------------------------------------------------------------------
# Render + send helpers
# ---------------------------------------------------------------------------

def render_html(template_name: str, **ctx) -> tuple[str, str]:
    """Returns (subject, html_body) by rendering a template.

    The subject lives in a `{% block subject %}` inside each template, so we
    render just that block to get the subject line, then render the full
    template for the HTML body. Both share the same context.
    """
    template = env.get_template(template_name)
    html = template.render(**ctx)
    # Render only the `subject` block. template.blocks maps each block name to
    # a render function; joining its output gives the block's text.
    if "subject" in template.blocks:
        context = template.new_context(ctx)
        subject = "".join(template.blocks["subject"](context)).strip()
    else:
        subject = template_name
    return subject, html


def send_email(to: str, subject: str, html: str, text: str = ""):
    msg = EmailMessage()
    msg["From"]    = formataddr((FROM_NAME, FROM_ADDR))
    msg["To"]      = to
    msg["Subject"] = subject
    if text:
        msg.set_content(text)
    else:
        msg.set_content(f"Please view this email in an HTML-capable mail client.\n\n{subject}")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.send_message(msg)
    print(f"   Sent to {to}: {subject!r}")


# ---------------------------------------------------------------------------
# Email-sending functions (what your app would call)
# ---------------------------------------------------------------------------

def send_welcome_email(to: str, name: str, verify_token: str):
    verify_url = f"https://myapp.example.com/verify?token={verify_token}"
    subject, html = render_html(
        "welcome.html",
        name=name,
        verify_url=verify_url,
    )
    plain = f"Hi {name},\n\nVerify your email: {verify_url}\n\n— My App"
    send_email(to, subject, html, plain)


def send_password_reset(to: str, name: str, reset_token: str, expires_minutes: int = 30):
    reset_url = f"https://myapp.example.com/reset?token={reset_token}"
    subject, html = render_html(
        "password_reset.html",
        name=name,
        email=to,
        reset_url=reset_url,
        expires_minutes=expires_minutes,
    )
    plain = (
        f"Hi {name},\n\n"
        f"Reset your password: {reset_url}\n"
        f"This link expires in {expires_minutes} minutes.\n\n— My App"
    )
    send_email(to, subject, html, plain)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 03 — Email Templates with Jinja2")
    print("=" * 60)

    print("\n1. Welcome email (new user signup):")
    send_welcome_email(
        to="newuser@example.com",
        name="Alex",
        verify_token="tok_abc123xyz",
    )

    print("\n2. Password reset email:")
    send_password_reset(
        to="alex@example.com",
        name="Alex",
        reset_token="reset_def456uvw",
        expires_minutes=30,
    )

    # ── Show how Jinja2 auto-escaping protects against injection ──────────
    print("\n3. Auto-escaping XSS attempt in name field:")
    send_welcome_email(
        to="hacker@example.com",
        name='<script>alert("xss")</script>',   # this will be escaped in the HTML
        verify_token="tok_safe",
    )
    print("   The <script> tag is escaped in the rendered HTML — open Mailpit to verify.")

    print("\nAll done. Open http://localhost:8025 to inspect rendered emails.")


if __name__ == "__main__":
    main()
