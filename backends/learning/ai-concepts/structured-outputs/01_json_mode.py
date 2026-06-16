"""Asking for JSON and parsing it — the simple, fragile way.

Run: `python 01_json_mode.py [anthropic|openai]`

The naive approach: instruct the model to return JSON, then `json.loads()` the
text. It usually works. But notice the things that can break it — a ```json fence,
a "Sure! Here is the JSON:" preamble, a trailing comment. This file deliberately
does only light cleanup so you can see how brittle "parse the text" is. The next
file ([02](02_pydantic_schema.py)) removes the guesswork with schema enforcement.
"""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROMPT = (
    "Extract the person's name, age (integer), and city from this text as JSON "
    'with keys "name", "age", "city". Return ONLY the JSON.\n\n'
    "Text: Maria is a 34-year-old engineer living in Lisbon."
)


def get_text(provider: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=256,
            messages=[{"role": "user", "content": PROMPT}],
        )
        return "".join(b.text for b in r.content if b.type == "text")

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=256,
        # OpenAI's "JSON mode": guarantees syntactically valid JSON (but not a
        # specific shape — that's what schema enforcement in 02 adds).
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": PROMPT}],
    )
    return r.choices[0].message.content


def strip_fences(text: str) -> str:
    """The kind of defensive cleanup you end up writing without schema enforcement."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for provider in ("anthropic", "openai"):
        if which not in (provider, "both"):
            continue
        print(f"\n=== {provider} ===")
        try:
            raw = get_text(provider)
        except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")
            continue
        print("raw text:", repr(raw))
        try:
            data = json.loads(strip_fences(raw))
            print("parsed dict:", data, "| age type:", type(data.get("age")).__name__)
        except json.JSONDecodeError as e:
            print("FAILED to parse:", e)


if __name__ == "__main__":
    main()
