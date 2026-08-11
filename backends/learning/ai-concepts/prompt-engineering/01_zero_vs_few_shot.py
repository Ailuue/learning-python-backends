"""Zero-shot vs few-shot prompting on the same classification task.

Run: `python 01_zero_vs_few_shot.py [anthropic|openai]`

Task: classify a support message as BILLING, BUG, or FEATURE — and return ONLY
that label. Zero-shot (just an instruction) often works but drifts in format
("This looks like a billing issue."). Few-shot (a few worked examples first) pins
the output down to exactly the label. Run both and compare.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

INPUTS = [
    "I was charged twice this month and want a refund.",
    "The export button does nothing when I click it.",
    "Any chance you could add dark mode?",
]

ZERO_SHOT = "Classify the support message as BILLING, BUG, or FEATURE."

# Few-shot: the instruction PLUS examples that demonstrate the exact output we want.
FEW_SHOT = """Classify the support message as BILLING, BUG, or FEATURE. Reply with the label only.

Message: My credit card was declined but I still got billed.
Label: BILLING

Message: The app crashes when I upload a PNG.
Label: BUG

Message: It would be great to have CSV export.
Label: FEATURE"""


def chat(provider: str, system: str, user: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=64,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in r.content if b.type == "text").strip()

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=64,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
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
            for text in INPUTS:
                zero = chat(provider, ZERO_SHOT, f"Message: {text}")
                few = chat(provider, FEW_SHOT, f"Message: {text}\nLabel:")
                print(f"  input : {text}")
                print(f"  zero  : {zero!r}")
                print(f"  few   : {few!r}")
        except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
