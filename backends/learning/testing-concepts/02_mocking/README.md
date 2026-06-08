# Mocking

## What is this?

Most backend code touches things that are slow, expensive, or unreliable in tests: databases, email services, payment APIs, external HTTP endpoints. You don't want to hit real Stripe every time you run your test suite.

**Mocking** replaces these dependencies with controlled fakes for the duration of a test. `unittest.mock` — part of Python's standard library — is the tool for this.

Three core concepts:

- **`patch`** — temporarily replaces a name in a module with a `MagicMock`. The original is restored automatically after the test.
- **`MagicMock`** — a fake object that records every call made to it. You control what it returns and can assert on how it was used.
- **`autospec`** — creates a mock that enforces the real object's interface, so tests catch bugs when the mocked code's signature changes.

## The golden rule

Patch where the name **is used**, not where it is defined.

```
# services.py defines EmailService
# checkout.py imports it:  from services import EmailService

patch("checkout.EmailService")   ✓  replaces the reference checkout holds
patch("services.EmailService")   ✗  checkout already holds its own reference
```

## What the files cover

| File | What it teaches |
|---|---|
| `services.py` | External dependencies (EmailService, PaymentService, WeatherClient) |
| `checkout.py` | Business logic that imports and uses those services |
| `test_01_patch.py` | `@patch`, `patch` as context manager, multiple patches, patching builtins |
| `test_02_mock_objects.py` | `MagicMock` directly, `return_value`, call assertions, chaining |
| `test_03_side_effects.py` | `side_effect` for sequences, exceptions, and dynamic callables |
| `test_04_autospec.py` | `spec`, `autospec` — catching interface drift between mock and real code |

## How to run

```bash
pytest 02_mocking/ -v
```
