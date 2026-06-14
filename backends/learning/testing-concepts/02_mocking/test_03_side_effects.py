"""
side_effect
===========
`side_effect` overrides `return_value` and runs when the mock is called.
It can be:

    A list       — values are returned one at a time on successive calls.
                   StopIteration is raised after the list is exhausted.
    An exception — the mock raises it instead of returning.
    A callable   — called with the same arguments; its return value is used.

side_effect takes precedence over return_value. If side_effect is set and
returns DEFAULT, return_value is used as a fallback.

Typical uses:
  - Simulate flaky services (fail once, succeed on retry)
  - Raise an exception on the Nth call
  - Return different values based on the argument passed

Run:
    pytest 02_mocking/test_03_side_effects.py -v
"""

from unittest.mock import MagicMock, DEFAULT
import pytest

from services import EmailService


# ---------------------------------------------------------------------------
# Code under test
# ---------------------------------------------------------------------------

def send_with_retry(email_service: EmailService, to: str, retries: int = 3) -> bool:
    for attempt in range(retries):
        try:
            return email_service.send(to=to, subject="Retry test", body="...")
        except ConnectionError:
            if attempt == retries - 1:
                raise
    return False


def fetch_price(api_client, item_id: str) -> float:
    response = api_client.get(f"/prices/{item_id}")
    return response["price"]


# ---------------------------------------------------------------------------
# 1. side_effect as a list — iterator of return values
# ---------------------------------------------------------------------------

def test_retry_succeeds_on_third_attempt():
    mock_service = MagicMock(spec=EmailService)
    # First two calls raise, third call returns True
    mock_service.send.side_effect = [
        ConnectionError("timeout"),
        ConnectionError("timeout"),
        True,
    ]

    result = send_with_retry(mock_service, "alice@example.com", retries=3)

    assert result is True
    assert mock_service.send.call_count == 3


def test_retry_reraises_after_all_attempts_exhausted():
    mock_service = MagicMock(spec=EmailService)
    mock_service.send.side_effect = ConnectionError("timeout")   # always fails

    with pytest.raises(ConnectionError):
        send_with_retry(mock_service, "alice@example.com", retries=3)


def test_different_return_value_per_call():
    mock_api = MagicMock()
    mock_api.get.side_effect = [
        {"price": 9.99},
        {"price": 14.99},
        {"price": 4.99},
    ]

    assert fetch_price(mock_api, "widget") == 9.99
    assert fetch_price(mock_api, "gadget") == 14.99
    assert fetch_price(mock_api, "doohickey") == 4.99


# ---------------------------------------------------------------------------
# 2. side_effect as an exception class or instance
# ---------------------------------------------------------------------------

def test_side_effect_raises_exception_class():
    mock_service = MagicMock(spec=EmailService)
    mock_service.send.side_effect = ConnectionError

    with pytest.raises(ConnectionError):
        mock_service.send(to="x@example.com", subject="s", body="b")


def test_side_effect_raises_exception_instance_with_message():
    mock_service = MagicMock(spec=EmailService)
    mock_service.send.side_effect = ConnectionError("SMTP server unreachable")

    with pytest.raises(ConnectionError, match="SMTP server unreachable"):
        mock_service.send(to="x@example.com", subject="s", body="b")


# ---------------------------------------------------------------------------
# 3. side_effect as a callable — dynamic response based on arguments
# ---------------------------------------------------------------------------

def test_side_effect_callable_based_on_args():
    mock_api = MagicMock()

    price_db = {
        "/prices/widget":   {"price": 9.99},
        "/prices/gadget":   {"price": 24.99},
    }

    def fake_get(path: str) -> dict:
        if path not in price_db:
            raise KeyError(f"Unknown path: {path}")
        return price_db[path]

    mock_api.get.side_effect = fake_get

    assert fetch_price(mock_api, "widget") == 9.99
    assert fetch_price(mock_api, "gadget") == 24.99

    with pytest.raises(KeyError):
        fetch_price(mock_api, "unknown_item")


# ---------------------------------------------------------------------------
# 4. Mixing side_effect with DEFAULT to fall back to return_value
# ---------------------------------------------------------------------------

def test_side_effect_falls_back_to_return_value():
    mock = MagicMock()
    mock.return_value = "default_response"

    call_count = {"n": 0}

    def conditional_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return "first_call_override"
        return DEFAULT   # fall through to return_value on subsequent calls

    mock.side_effect = conditional_effect

    assert mock() == "first_call_override"
    assert mock() == "default_response"
    assert mock() == "default_response"
