"""
patch
=====
`unittest.mock.patch` temporarily replaces an object in a module's namespace
with a MagicMock for the duration of a test, then restores the original.

Three forms:
    @patch("module.Name")               decorator — mock injected as last param
    with patch("module.Name") as mock:  context manager — mock in block scope
    patch.object(obj, "attr_name")      patch a method on a specific object

The golden rule: patch at the *usage site*, not the definition site.
checkout.py does:  from services import EmailService
So patch:          "checkout.EmailService"   ✓
Not:               "services.EmailService"   ✗  (checkout already holds its own ref)

Multiple @patch decorators stack: inner decorator → first parameter,
outer decorator → second parameter (they inject in bottom-up order).

Run:
    pytest 02_mocking/test_01_patch.py -v
"""

import time
from unittest.mock import patch, call

import pytest

import checkout


# ---------------------------------------------------------------------------
# 1. @patch as a decorator
# ---------------------------------------------------------------------------

class TestRegisterUser:
    @patch("checkout.EmailService")
    def test_sends_welcome_email(self, MockEmailService):
        # MockEmailService is the patched class.
        # .return_value is the instance that checkout.EmailService() creates.
        mock_instance = MockEmailService.return_value
        mock_instance.send_welcome.return_value = True

        result = checkout.register_user("alice@example.com")

        assert result["status"] == "active"
        mock_instance.send_welcome.assert_called_once_with("alice@example.com")

    @patch("checkout.EmailService")
    def test_returns_user_dict_with_email(self, MockEmailService):
        MockEmailService.return_value.send_welcome.return_value = True

        result = checkout.register_user("bob@example.com")

        assert result["email"] == "bob@example.com"

    @patch("checkout.EmailService")
    def test_email_service_instantiated_once(self, MockEmailService):
        checkout.register_user("carol@example.com")
        MockEmailService.assert_called_once()   # class was instantiated exactly once


# ---------------------------------------------------------------------------
# 2. patch as a context manager
# ---------------------------------------------------------------------------

def test_complete_purchase_success():
    with patch("checkout.PaymentService") as MockPayment:
        MockPayment.return_value.charge.return_value = {
            "status": "success",
            "charge_id": "ch_abc123",
        }
        result = checkout.complete_purchase(
            user_id=1, amount_cents=5000, card_token="tok_visa"
        )

    assert result["charge_id"] == "ch_abc123"
    assert result["order_id"] == 100


def test_complete_purchase_raises_on_failure():
    with patch("checkout.PaymentService") as MockPayment:
        MockPayment.return_value.charge.return_value = {
            "status": "declined",
            "charge_id": None,
        }
        with pytest.raises(RuntimeError, match="Payment failed"):
            checkout.complete_purchase(user_id=1, amount_cents=5000, card_token="tok_bad")


def test_weather_alert_extreme_heat():
    with patch("checkout.WeatherClient") as MockClient:
        MockClient.return_value.get_temperature.return_value = 42.0
        alert = checkout.get_weather_alert("Phoenix")
    assert alert is not None
    assert "Extreme heat" in alert
    assert "42.0" in alert


def test_no_alert_in_normal_range():
    with patch("checkout.WeatherClient") as MockClient:
        MockClient.return_value.get_temperature.return_value = 20.0
        assert checkout.get_weather_alert("London") is None


# ---------------------------------------------------------------------------
# 3. Multiple @patch decorators — bottom decorator injects first
# ---------------------------------------------------------------------------

@patch("checkout.PaymentService")    # outer → second param
@patch("checkout.EmailService")      # inner → first param
def test_register_does_not_touch_payment(MockEmail, MockPayment):
    checkout.register_user("alice@example.com")
    # Proves register_user never calls the payment service.
    MockPayment.return_value.charge.assert_not_called()


# ---------------------------------------------------------------------------
# 4. Patching a built-in (time.sleep)
#    Without mocking, test_slow_path would pause for 10 real seconds.
# ---------------------------------------------------------------------------

def slow_health_check() -> str:
    time.sleep(10)
    return "ok"


@patch("time.sleep")
def test_health_check_does_not_wait(mock_sleep):
    result = slow_health_check()
    assert result == "ok"
    mock_sleep.assert_called_once_with(10)


# ---------------------------------------------------------------------------
# 5. patch.object — patch a method on an already-instantiated object
# ---------------------------------------------------------------------------

def test_patch_object_on_instance():
    client = checkout.WeatherClient()

    with patch.object(client, "get_temperature", return_value=5.0):
        # is_hot checks get_temperature > 30; 5.0 is not hot
        assert client.is_hot("Oslo") is False
