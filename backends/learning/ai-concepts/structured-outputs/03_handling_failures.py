"""When structured output still goes wrong: validate, detect, retry.

Run: `python 03_handling_failures.py [anthropic|openai]`

Schema enforcement removes most failures, but not all. In production you still
guard against:
  - INVALID DATA: a value that parses as JSON but fails your stricter rules
    (Pydantic raises ValidationError) -> retry with the error as feedback.
  - TRUNCATION: the model hit max_tokens mid-object -> the JSON is incomplete.
    Detect via the stop/finish reason, don't just let json.loads explode.
  - REFUSAL: the model declined for safety reasons -> there's no data to parse;
    surface it, don't retry the same prompt.

To make the failure path visible, this example does NOT use schema-enforced
parsing — it asks for JSON, validates with Pydantic, and retries on invalid
output, feeding the validation error back to the model. That retry-on-invalid
loop is a useful pattern even when you do use enforcement.
"""
import os
import sys

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator

load_dotenv()


class Product(BaseModel):
    name: str
    price_usd: float

    @field_validator("price_usd")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price_usd must be >= 0")
        return v


BASE_PROMPT = (
    'Return JSON with keys "name" (string) and "price_usd" (number) for: '
    "a mechanical keyboard that costs forty-nine dollars ninety-nine. Return ONLY JSON."
)


def call(provider: str, prompt: str) -> tuple[str, str]:
    """Returns (text, stop_reason). stop_reason flags refusal / truncation."""
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        if r.stop_reason == "refusal":
            return "", "refusal"
        text = "".join(b.text for b in r.content if b.type == "text")
        # stop_reason is Optional in the SDK; "unknown" keeps the contract str.
        return text, r.stop_reason or "unknown"  # "end_turn", or "max_tokens" if truncated

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=256,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": prompt}],
    )
    choice = r.choices[0]
    # content is None on a content-filter stop — exactly the failure this file is
    # about, so hand it back as empty text alongside the finish_reason that explains it.
    return choice.message.content or "", choice.finish_reason  # "stop", or "length" if truncated


def get_product(provider: str, max_attempts: int = 3) -> Product:
    prompt = BASE_PROMPT
    for attempt in range(1, max_attempts + 1):
        text, reason = call(provider, prompt)

        if reason == "refusal":
            raise RuntimeError("model refused the request — not retrying")
        if reason in ("max_tokens", "length"):
            print(f"  attempt {attempt}: response truncated; raising max_tokens would help")

        try:
            return Product.model_validate_json(_strip_fences(text))
        except (ValidationError, ValueError) as e:
            print(f"  attempt {attempt}: invalid ({type(e).__name__}); feeding error back")
            # Retry: tell the model exactly what was wrong with its last output.
            prompt = f"{BASE_PROMPT}\n\nYour previous answer was invalid: {e}\nFix it."

    raise RuntimeError(f"gave up after {max_attempts} attempts")


def _strip_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    return text


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for provider in ("anthropic", "openai"):
        if which not in (provider, "both"):
            continue
        print(f"\n=== {provider} ===")
        try:
            print("  got:", get_product(provider))
        except Exception as e:  # RuntimeError (gave up / refusal) or API error (e.g. 429)
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
