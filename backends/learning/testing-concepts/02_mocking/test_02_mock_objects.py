"""
MagicMock
=========
MagicMock is the object you get back from patch(). You can also create one
directly when you want to hand a fake dependency to code under test.

Key attributes and methods:
    mock.return_value           what the mock returns when called: mock()
    mock.method.return_value    what mock.method() returns
    mock()                      records the call; returns return_value

Call assertions (raise AssertionError if not satisfied):
    mock.assert_called()                   called at least once
    mock.assert_called_once()              called exactly once
    mock.assert_called_with(*a, **kw)      last call used these args
    mock.assert_called_once_with(*a, **kw) called once with these args
    mock.assert_not_called()               never called

Call introspection (don't raise — query the recorded calls yourself):
    mock.call_count          integer
    mock.call_args           args of the most recent call
    mock.call_args_list      list of call(*args, **kwargs) objects

Run:
    pytest 02_mocking/test_02_mock_objects.py -v
"""

from unittest.mock import MagicMock, call


from services import EmailService, PaymentService


# ---------------------------------------------------------------------------
# 1. Creating a MagicMock directly (dependency injection style)
# ---------------------------------------------------------------------------

def send_notification(email_service: EmailService, user_email: str, message: str) -> None:
    email_service.send(to=user_email, subject="Notification", body=message)


def test_send_notification_calls_send():
    mock_service = MagicMock(spec=EmailService)

    send_notification(mock_service, "alice@example.com", "Your order shipped.")

    mock_service.send.assert_called_once_with(
        to="alice@example.com",
        subject="Notification",
        body="Your order shipped.",
    )


# ---------------------------------------------------------------------------
# 2. return_value — control what the mock returns when called
# ---------------------------------------------------------------------------

def process_payment(payment_service: PaymentService, amount: int, token: str) -> str:
    result = payment_service.charge(amount, token)
    return result["charge_id"]


def test_process_payment_returns_charge_id():
    mock_payment = MagicMock(spec=PaymentService)
    mock_payment.charge.return_value = {"status": "success", "charge_id": "ch_xyz"}

    charge_id = process_payment(mock_payment, 1000, "tok_abc")

    assert charge_id == "ch_xyz"


# ---------------------------------------------------------------------------
# 3. Call count and call_args inspection
# ---------------------------------------------------------------------------

def batch_notify(email_service: EmailService, emails: list[str]) -> None:
    for email in emails:
        email_service.send(to=email, subject="Batch", body="Hello")


def test_batch_notify_calls_send_for_each_email():
    mock_service = MagicMock(spec=EmailService)
    emails = ["a@x.com", "b@x.com", "c@x.com"]

    batch_notify(mock_service, emails)

    assert mock_service.send.call_count == 3


def test_batch_notify_sends_to_correct_addresses():
    mock_service = MagicMock(spec=EmailService)
    emails = ["a@x.com", "b@x.com"]

    batch_notify(mock_service, emails)

    expected_calls = [
        call(to="a@x.com", subject="Batch", body="Hello"),
        call(to="b@x.com", subject="Batch", body="Hello"),
    ]
    mock_service.send.assert_has_calls(expected_calls, any_order=False)


# ---------------------------------------------------------------------------
# 4. assert_not_called — verify a path is NOT taken
# ---------------------------------------------------------------------------

def notify_if_opted_in(email_service: EmailService, email: str, opted_in: bool) -> None:
    if opted_in:
        email_service.send(to=email, subject="News", body="...")


def test_opted_out_user_receives_no_email():
    mock_service = MagicMock(spec=EmailService)
    notify_if_opted_in(mock_service, "alice@example.com", opted_in=False)
    mock_service.send.assert_not_called()


def test_opted_in_user_receives_email():
    mock_service = MagicMock(spec=EmailService)
    notify_if_opted_in(mock_service, "bob@example.com", opted_in=True)
    mock_service.send.assert_called_once()


# ---------------------------------------------------------------------------
# 5. Attribute access on MagicMock is auto-created
#    Every attribute of a MagicMock is itself a MagicMock — useful but
#    also a footgun: typos in method names won't raise AttributeError.
# ---------------------------------------------------------------------------

def test_auto_created_attributes():
    mock = MagicMock()

    # Accessing any attribute gives a new MagicMock (no AttributeError).
    result = mock.nonexistent_method("arg1", "arg2")

    # The call was recorded even though the method doesn't exist.
    mock.nonexistent_method.assert_called_once_with("arg1", "arg2")

    # The return value is also a MagicMock (truthy, not None).
    assert result is not None


# ---------------------------------------------------------------------------
# 6. Chained calls — mock.method().attribute.other_method()
# ---------------------------------------------------------------------------

def get_user_email_domain(payment_service: PaymentService, charge_id: str) -> str:
    # Hypothetical: payment_service.get_charge(id).customer.email
    email = payment_service.get_charge(charge_id).customer.email
    return email.split("@")[1]


def test_chained_return_values():
    mock_payment = MagicMock()
    mock_payment.get_charge.return_value.customer.email = "alice@example.com"

    domain = get_user_email_domain(mock_payment, "ch_123")

    assert domain == "example.com"
    mock_payment.get_charge.assert_called_once_with("ch_123")
