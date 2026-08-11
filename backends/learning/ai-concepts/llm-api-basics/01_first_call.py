"""The smallest possible LLM call, against both providers.

Run: `python 01_first_call.py [anthropic|openai]` (no arg = both).

The point of this file: a request is just a list of role-tagged messages, and the
response is an object you dig the text out of. The two SDKs differ only in how
that object is shaped.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # pulls API keys + model names from ../.env

PROMPT = "In one sentence, what is a backend engineer?"


def call_anthropic() -> str:
    import anthropic

    print(
        f"Using Anthropic model: {os.environ.get('ANTHROPIC_MODEL', 'claude-opus-4-8')}"
    )
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    resp = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
        max_tokens=1024,  # a hard cap on the *response* length, in tokens
        messages=[{"role": "user", "content": PROMPT}],
    )
    # resp.content is a LIST of blocks (text, tool_use, ...). Grab the text ones.
    return "".join(block.text for block in resp.content if block.type == "text")


def call_openai() -> str:
    from openai import OpenAI

    print(f"Using OpenAI model: {os.environ.get('OPENAI_MODEL', 'gpt-4o')}")
    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    resp = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": PROMPT}],
    )
    # OpenAI returns one or more "choices"; the text is on the first choice.
    # content is None on a refusal or a tool-call-only reply, so check it.
    content = resp.choices[0].message.content
    if content is None:
        raise RuntimeError("model returned no text content")
    return content


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    providers = {"anthropic": call_anthropic, "openai": call_openai}

    for name, fn in providers.items():
        if which in (name, "both"):
            print(f"\n=== {name} ===")
            try:
                print(fn())
            except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
                print(
                    f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]"
                )


if __name__ == "__main__":
    main()
