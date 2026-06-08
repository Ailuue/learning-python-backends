"""
Business logic that uses the external services.

These functions create service instances internally. The tests must patch
at the import site (checkout.EmailService, not services.EmailService) because
checkout holds its own reference to the name after the `from ... import`.
"""
from services import EmailService, PaymentService, WeatherClient


def register_user(email: str) -> dict:
    service = EmailService()
    user = {"id": 1, "email": email, "status": "active"}
    service.send_welcome(email)
    return user


def complete_purchase(user_id: int, amount_cents: int, card_token: str) -> dict:
    service = PaymentService()
    charge = service.charge(amount_cents, card_token)
    if charge["status"] != "success":
        raise RuntimeError(f"Payment failed: {charge}")
    return {
        "order_id": 100,
        "user_id": user_id,
        "charge_id": charge["charge_id"],
    }


def get_weather_alert(city: str) -> str | None:
    client = WeatherClient()
    temp = client.get_temperature(city)
    if temp > 40:
        return f"Extreme heat warning for {city}: {temp}°C"
    if temp < -10:
        return f"Extreme cold warning for {city}: {temp}°C"
    return None
