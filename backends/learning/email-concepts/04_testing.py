"""
Concept 04 — Testing Email

There are two complementary strategies for testing email in a backend app:

  UNIT TESTS — mock smtplib so no real connection is made.
    Fast, isolated, CI-friendly. Assert that the right message was constructed
    and that SMTP was called with the right arguments.

  INTEGRATION TESTS — send to Mailpit and query its HTTP API to assert receipt.
    Catches real rendering bugs (wrong template, broken HTML). Requires Docker.

Neither replaces the other:
  - Unit tests verify your *code* behaves correctly.
  - Integration tests verify the *email* looks right end-to-end.

This file demonstrates both patterns using Python's `unittest` and `unittest.mock`.

HOW TO RUN:
  docker compose up -d          ← needed for integration tests only
  python 04_testing.py
"""

import json
import smtplib
import unittest
import urllib.request
from email.message import EmailMessage
from email.utils import formataddr
from unittest.mock import MagicMock, patch, call

SMTP_HOST   = "localhost"
SMTP_PORT   = 1025
MAILPIT_API = "http://localhost:8025/api/v1"


# ---------------------------------------------------------------------------
# The application code under test
# (Imagine this lives in your app's email module)
# ---------------------------------------------------------------------------

def send_welcome_email(smtp_host: str, smtp_port: int, to: str, name: str):
    """Builds and sends a welcome email. Returns the EmailMessage sent."""
    msg = EmailMessage()
    msg["From"]    = formataddr(("My App", "app@example.com"))
    msg["To"]      = to
    msg["Subject"] = f"Welcome to My App, {name}!"
    msg.set_content(f"Hi {name}, thanks for signing up!")
    msg.add_alternative(
        f"<h1>Hi {name}!</h1><p>Thanks for signing up!</p>",
        subtype="html",
    )
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.send_message(msg)
    return msg


def send_password_reset(smtp_host: str, smtp_port: int, to: str, token: str):
    msg = EmailMessage()
    msg["From"]    = "app@example.com"
    msg["To"]      = to
    msg["Subject"] = "Reset your password"
    msg.set_content(f"Your reset link: https://example.com/reset?token={token}")
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.send_message(msg)
    return msg


# ---------------------------------------------------------------------------
# UNIT TESTS — mock smtplib, no real connection
# ---------------------------------------------------------------------------

class TestSendWelcomeEmail(unittest.TestCase):

    @patch("smtplib.SMTP")
    def test_sends_to_correct_recipient(self, MockSMTP):
        """The message must be addressed to the given recipient."""
        mock_conn = MockSMTP.return_value.__enter__.return_value

        msg = send_welcome_email("localhost", 1025, "alex@example.com", "Alex")

        # SMTP was constructed with the right host and port
        MockSMTP.assert_called_once_with("localhost", 1025)
        # send_message was called once with our EmailMessage
        mock_conn.send_message.assert_called_once_with(msg)
        self.assertEqual(msg["To"], "alex@example.com")

    @patch("smtplib.SMTP")
    def test_subject_contains_name(self, MockSMTP):
        msg = send_welcome_email("localhost", 1025, "x@example.com", "Dana")
        self.assertIn("Dana", msg["Subject"])

    @patch("smtplib.SMTP")
    def test_message_has_html_part(self, MockSMTP):
        """Email must include an HTML alternative part."""
        msg = send_welcome_email("localhost", 1025, "x@example.com", "Jordan")
        content_types = [part.get_content_type() for part in msg.walk()]
        self.assertIn("text/html", content_types)

    @patch("smtplib.SMTP")
    def test_smtp_connection_is_closed(self, MockSMTP):
        """The `with` block must close the connection even if send fails."""
        mock_conn = MockSMTP.return_value.__enter__.return_value
        mock_conn.send_message.side_effect = smtplib.SMTPException("server busy")

        with self.assertRaises(smtplib.SMTPException):
            send_welcome_email("localhost", 1025, "x@example.com", "Alex")

        # __exit__ must still be called (context manager protocol)
        MockSMTP.return_value.__exit__.assert_called_once()


class TestSendPasswordReset(unittest.TestCase):

    @patch("smtplib.SMTP")
    def test_reset_link_in_body(self, MockSMTP):
        token = "tok_secret_xyz"
        msg = send_password_reset("localhost", 1025, "user@example.com", token)
        body = msg.get_body(preferencelist=("plain",)).get_content()
        self.assertIn(token, body)
        self.assertIn("https://example.com/reset", body)

    @patch("smtplib.SMTP")
    def test_subject_line(self, MockSMTP):
        msg = send_password_reset("localhost", 1025, "user@example.com", "tok")
        self.assertEqual(msg["Subject"], "Reset your password")


# ---------------------------------------------------------------------------
# INTEGRATION TESTS — send to Mailpit, query its API to verify delivery
# ---------------------------------------------------------------------------

def mailpit_get_messages():
    """Fetch the list of messages from Mailpit's REST API."""
    with urllib.request.urlopen(f"{MAILPIT_API}/messages") as resp:
        return json.loads(resp.read())


def mailpit_delete_all():
    """Delete all messages from Mailpit (clean slate before each test)."""
    req = urllib.request.Request(
        f"{MAILPIT_API}/messages",
        method="DELETE",
    )
    urllib.request.urlopen(req)


class TestIntegrationSendWelcomeEmail(unittest.TestCase):
    """
    Requires docker compose up.
    These tests actually send to Mailpit and assert using its HTTP API.
    """

    def setUp(self):
        try:
            mailpit_delete_all()
        except Exception:
            self.skipTest("Mailpit not running — start with `docker compose up -d`")

    def test_email_arrives_in_mailpit(self):
        send_welcome_email(SMTP_HOST, SMTP_PORT, "alex@example.com", "Alex")
        data = mailpit_get_messages()
        self.assertEqual(data["total"], 1)
        msg = data["messages"][0]
        self.assertEqual(msg["To"][0]["Address"], "alex@example.com")
        self.assertIn("Welcome", msg["Subject"])

    def test_html_and_text_parts_present(self):
        send_welcome_email(SMTP_HOST, SMTP_PORT, "test@example.com", "Tester")
        data = mailpit_get_messages()
        msg_summary = data["messages"][0]
        # Fetch the full message to inspect parts
        with urllib.request.urlopen(
            f"{MAILPIT_API}/message/{msg_summary['ID']}"
        ) as resp:
            full = json.loads(resp.read())
        content_types = [p["ContentType"] for p in full.get("Attachments", [])]
        # Mailpit exposes HTML in the top-level field
        self.assertTrue(full.get("HTML"), "Expected HTML part to be non-empty")
        self.assertTrue(full.get("Text"), "Expected plain-text part to be non-empty")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 04 — Testing Email")
    print("=" * 60)
    print()

    loader = unittest.TestLoader()
    suite  = unittest.TestSuite()

    print("Running UNIT tests (no server needed):")
    unit_suite = loader.loadTestsFromTestCase(TestSendWelcomeEmail)
    unit_suite.addTests(loader.loadTestsFromTestCase(TestSendPasswordReset))
    runner = unittest.TextTestRunner(verbosity=2)
    unit_result = runner.run(unit_suite)

    print("\nRunning INTEGRATION tests (requires docker compose up):")
    int_suite = loader.loadTestsFromTestCase(TestIntegrationSendWelcomeEmail)
    runner.run(int_suite)


if __name__ == "__main__":
    main()
