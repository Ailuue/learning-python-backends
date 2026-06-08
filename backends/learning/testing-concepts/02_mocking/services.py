"""
External service dependencies.

These classes represent boundaries where the code talks to the outside world:
SMTP servers, payment processors, third-party APIs. In production they do
real work; in tests we replace them with mocks.
"""
import time
import random


class EmailService:
    def send(self, to: str, subject: str, body: str) -> bool:
        time.sleep(0.2)   # real SMTP latency
        print(f"[EMAIL] → {to}: {subject}")
        return True

    def send_welcome(self, user_email: str) -> bool:
        return self.send(
            to=user_email,
            subject="Welcome!",
            body=f"Hi {user_email}, welcome to the platform.",
        )


class PaymentService:
    def charge(self, amount_cents: int, card_token: str) -> dict:
        time.sleep(0.5)   # real Stripe latency
        return {
            "status": "success",
            "charge_id": f"ch_{random.randint(10000, 99999)}",
        }

    def refund(self, charge_id: str) -> dict:
        time.sleep(0.3)
        return {"status": "refunded", "charge_id": charge_id}


class WeatherClient:
    def get_temperature(self, city: str) -> float:
        raise NotImplementedError("Requires a live API key and network access")

    def is_hot(self, city: str) -> bool:
        return self.get_temperature(city) > 30.0
