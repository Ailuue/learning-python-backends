"""Output validation: treat the model's response as untrusted input.

Run: `python 02_output_validation.py [anthropic|openai]`

Even with no attacker, model output can be wrong in ways your code must catch
before acting on it:
  - off allow-list: a label outside the set you support (hallucinated category),
  - too long: an unbounded blob where you expected a short value,
  - leaking PII/secrets: an email, card number, or key in the text.

We run a real classification and validate the label against an allow-list (reject
anything else), then run the same validators over a crafted string to show the
PII/length checks firing. The pattern: validate -> on failure, fall back or
regenerate; never pass unvalidated model output to the next step.
"""
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()

ALLOWED_LABELS = {"BILLING", "BUG", "FEATURE"}
MAX_LEN = 200

# Crude PII/secret patterns — illustrative, not exhaustive. Real systems use a
# dedicated scanner, but the principle (scan before trusting) is the point.
PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "credit_card": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "api_key": re.compile(r"\b(sk|pa)-[A-Za-z0-9]{8,}\b"),
}


def find_violations(text: str, *, allow_labels: bool = False) -> list[str]:
    problems = []
    if allow_labels and text.upper() not in ALLOWED_LABELS:
        problems.append(f"label {text.upper()!r} not in allow-list {sorted(ALLOWED_LABELS)}")
    if len(text) > MAX_LEN:
        problems.append(f"too long ({len(text)} > {MAX_LEN} chars)")
    for name, pattern in PATTERNS.items():
        if pattern.search(text):
            problems.append(f"contains possible {name}")
    return problems


def classify(provider: str, text: str) -> str:
    system = "Classify the message as BILLING, BUG, or FEATURE. Reply with the label only."
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=16,
            system=system,
            messages=[{"role": "user", "content": text}],
        )
        return "".join(b.text for b in r.content if b.type == "text").strip()

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=16,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": text}],
    )
    content = r.choices[0].message.content
    if content is None:
        raise RuntimeError("model returned no text content")
    return content.strip()


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"

    for provider in ("anthropic", "openai"):
        if which not in (provider, "both"):
            continue
        print(f"\n=== {provider} ===")
        try:
            label = classify(provider, "I was double charged this month")
            violations = find_violations(label, allow_labels=True)
            verdict = "ACCEPT" if not violations else f"REJECT ({'; '.join(violations)})"
            print(f"  model label: {label!r} -> {verdict}")
        except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")

    # Same validators over a deliberately bad string, so the PII/length checks fire.
    print("\n--- validators on a crafted bad output ---")
    bad = "Sure! Contact the user at jane.doe@example.com or call 4111 1111 1111 1111."
    print(f"  input: {bad!r}")
    print(f"  violations: {find_violations(bad)}")


if __name__ == "__main__":
    main()
