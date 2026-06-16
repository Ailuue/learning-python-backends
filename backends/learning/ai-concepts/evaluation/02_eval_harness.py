"""A tiny eval harness: run a fixed test set, score it, report accuracy.

Run: `python 02_eval_harness.py [anthropic|openai]`

This is the regression test for a prompt. We have a DATASET of inputs with known
correct labels. We run each through the model under test, compare the output to the
expected label programmatically (no judge needed — the answer is exact), and print
an accuracy number.

The workflow this enables: change the SYSTEM prompt below, re-run, and watch the
accuracy move. That number is how you tell a real improvement from a vibe.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# The fixed evaluation set: (input, expected label). Grow this over time with every
# real-world case that surprised you — that's how the suite gets valuable.
DATASET = [
    ("I want a refund for my subscription", "BILLING"),
    ("The page crashes when I hit save", "BUG"),
    ("Please add a dark theme", "FEATURE"),
    ("My invoice has the wrong amount", "BILLING"),
    ("Login button does nothing on mobile", "BUG"),
]

# The prompt under test. Tweak this and re-run to see accuracy change.
SYSTEM = "Classify the support message as exactly one of: BILLING, BUG, FEATURE. Reply with the label only."


def classify(provider: str, text: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=16,
            system=SYSTEM,
            messages=[{"role": "user", "content": text}],
        )
        return "".join(b.text for b in r.content if b.type == "text").strip().upper()

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=16,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}],
    )
    return r.choices[0].message.content.strip().upper()


def evaluate(provider: str) -> None:
    correct = 0
    for text, expected in DATASET:
        got = classify(provider, text)
        ok = got == expected
        correct += ok
        print(f"  {'✓' if ok else '✗'} expected={expected:<8} got={got:<8} | {text}")
    pct = 100 * correct / len(DATASET)
    print(f"  accuracy: {correct}/{len(DATASET)} = {pct:.0f}%")


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for provider in ("anthropic", "openai"):
        if which in (provider, "both"):
            print(f"\n=== {provider} ===")
            try:
                evaluate(provider)
            except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
                print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
