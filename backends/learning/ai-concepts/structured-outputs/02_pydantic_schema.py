"""Schema-enforced output: define a Pydantic model, get back a validated object.

Run: `python 02_pydantic_schema.py [anthropic|openai]`

This is the production answer to "I need data, not text." You define the shape
ONCE as a Pydantic model and hand it to the SDK's parse helper. The provider
constrains generation to match the schema, and the SDK returns a validated
instance — no fences, no preamble, no `json.loads`, no guessing about types.

Both SDKs accept the *same* Pydantic model; only the method name and where the
result lands differ:
  - Anthropic: `client.messages.parse(..., output_format=Model)` -> `.parsed_output`
  - OpenAI:    `client.beta.chat.completions.parse(..., response_format=Model)`
               -> `.choices[0].message.parsed`
"""
import os
import sys
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class SupportTicket(BaseModel):
    """The exact shape we want back. Field types and the enum are enforced."""

    summary: str
    category: Literal["BILLING", "BUG", "FEATURE"]
    priority: Literal["low", "medium", "high"]
    needs_human: bool


TEXT = (
    "Subject: URGENT - double charged!! I've been billed twice for my annual plan "
    "and need this refunded today, I'm furious."
)
INSTRUCTION = f"Extract a structured support ticket from this message.\n\n{TEXT}"


def parse_anthropic() -> SupportTicket:
    import anthropic

    client = anthropic.Anthropic()
    r = client.messages.parse(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
        max_tokens=512,
        messages=[{"role": "user", "content": INSTRUCTION}],
        output_format=SupportTicket,
    )
    return r.parsed_output


def parse_openai() -> SupportTicket:
    from openai import OpenAI

    client = OpenAI()
    r = client.beta.chat.completions.parse(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=512,
        messages=[{"role": "user", "content": INSTRUCTION}],
        response_format=SupportTicket,
    )
    return r.choices[0].message.parsed


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for provider, fn in {"anthropic": parse_anthropic, "openai": parse_openai}.items():
        if which not in (provider, "both"):
            continue
        print(f"\n=== {provider} ===")
        try:
            ticket = fn()  # already a validated SupportTicket instance
            print(ticket)
            # Because it's a real object, your code can branch on it with confidence:
            if ticket.needs_human and ticket.priority == "high":
                print("  -> routing to a human agent immediately")
        except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
