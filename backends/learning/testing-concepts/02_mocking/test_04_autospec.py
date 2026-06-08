"""
autospec
========
A plain MagicMock accepts any attribute access and any call signature.
That means a typo in a method name or wrong number of arguments silently
passes — the test never notices.

spec=RealClass limits attribute access to what the real class has, but
still doesn't enforce method signatures.

autospec=True (or create_autospec()) enforces the full interface: attribute
names AND method signatures must match the real class. Tests catch bugs when
the mocked code's interface drifts from the mock's expectations.

When to use autospec:
  - You're mocking a class or function whose interface might change.
  - You want confidence that if the real method adds/removes a parameter,
    the test will fail loudly instead of silently passing.

When NOT to use autospec:
  - Mocking objects that are dynamically constructed at runtime.
  - Mocking external C extensions (autospec can't inspect them reliably).
  - The overhead is overkill for a simple one-call smoke test.

Run:
    pytest 02_mocking/test_04_autospec.py -v
"""

from unittest.mock import MagicMock, create_autospec, patch

import pytest

from services import EmailService, PaymentService


# ---------------------------------------------------------------------------
# 1. The problem with plain MagicMock: typos pass silently
# ---------------------------------------------------------------------------

def test_plain_mock_accepts_misspelled_method():
    mock = MagicMock()
    # "sned" is a typo for "send" — but MagicMock doesn't know or care.
    mock.sned("oops")
    # No error. The test passes. The bug goes undetected.
    mock.sned.assert_called_once()


# ---------------------------------------------------------------------------
# 2. spec= limits attribute access but not argument checking
# ---------------------------------------------------------------------------

def test_spec_catches_nonexistent_attribute():
    mock = MagicMock(spec=EmailService)

    with pytest.raises(AttributeError):
        mock.sned("oops")   # "sned" does not exist on EmailService


def test_spec_does_not_catch_wrong_argument_count():
    mock = MagicMock(spec=EmailService)
    # EmailService.send takes (to, subject, body) — but spec doesn't enforce this.
    mock.send("only_one_arg")   # no error raised
    mock.send.assert_called_once_with("only_one_arg")


# ---------------------------------------------------------------------------
# 3. autospec enforces method signatures
# ---------------------------------------------------------------------------

def test_autospec_catches_wrong_argument_count():
    mock = create_autospec(EmailService)

    with pytest.raises(TypeError):
        # send() requires (to, subject, body) — passing only one arg raises TypeError
        mock.send("only_one_arg")


def test_autospec_catches_nonexistent_method():
    mock = create_autospec(EmailService)

    with pytest.raises(AttributeError):
        mock.sned("typo")


def test_autospec_accepts_correct_call():
    mock = create_autospec(EmailService)
    mock.send.return_value = True

    result = mock.send(to="alice@example.com", subject="Hi", body="Hello")

    assert result is True
    mock.send.assert_called_once_with(
        to="alice@example.com", subject="Hi", body="Hello"
    )


# ---------------------------------------------------------------------------
# 4. autospec=True inside @patch
# ---------------------------------------------------------------------------

@patch("checkout.EmailService", autospec=True)
def test_register_user_with_autospec(MockEmailService):
    from checkout import register_user

    mock_instance = MockEmailService.return_value
    mock_instance.send_welcome.return_value = True

    result = register_user("alice@example.com")

    assert result["status"] == "active"
    mock_instance.send_welcome.assert_called_once_with("alice@example.com")


@patch("checkout.PaymentService", autospec=True)
def test_charge_called_with_correct_args(MockPaymentService):
    from checkout import complete_purchase

    mock_instance = MockPaymentService.return_value
    mock_instance.charge.return_value = {"status": "success", "charge_id": "ch_789"}

    complete_purchase(user_id=1, amount_cents=2000, card_token="tok_xyz")

    mock_instance.charge.assert_called_once_with(2000, "tok_xyz")


# ---------------------------------------------------------------------------
# 5. create_autospec for a standalone function (not a class)
# ---------------------------------------------------------------------------

def compute_discount(price: float, pct: float) -> float:
    return price * (1 - pct / 100)


def test_autospec_on_function():
    mock_fn = create_autospec(compute_discount)
    mock_fn.return_value = 80.0

    result = mock_fn(100.0, 20.0)

    assert result == 80.0
    mock_fn.assert_called_once_with(100.0, 20.0)


def test_autospec_function_rejects_wrong_arity():
    mock_fn = create_autospec(compute_discount)

    with pytest.raises(TypeError):
        mock_fn(100.0)   # missing second argument
