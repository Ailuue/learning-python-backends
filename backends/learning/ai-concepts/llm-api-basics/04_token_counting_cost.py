"""Counting tokens and estimating cost.

Run: `python 04_token_counting_cost.py [anthropic|openai]`

You pay per token — both for what you send (input) and what you get back
(output), at different rates. Two skills matter:

  1. Counting tokens BEFORE you send, so you can reject an over-budget request or
     pick a cheaper model. Anthropic has a dedicated `count_tokens` endpoint.
     OpenAI doesn't — you count locally with the `tiktoken` library (its
     tokenizer). NOTE: tiktoken is OpenAI's tokenizer and is WRONG for Claude —
     never use it to estimate Anthropic tokens; use the count_tokens endpoint.
  2. Reading actual usage AFTER the call (`usage` on the response) and turning it
     into dollars.

Prices below are illustrative and change often — always check the provider's
pricing page. They live here only to show the arithmetic.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROMPT = "Summarize the CAP theorem for a backend engineer in 3 bullet points."

# USD per 1,000,000 tokens (input, output). Illustrative — verify current pricing.
PRICES = {
    "anthropic": {"input": 5.00, "output": 25.00},   # Claude Opus tier
    "openai": {"input": 2.50, "output": 10.00},       # GPT-4o tier
}


def dollars(provider: str, in_tok: int, out_tok: int) -> float:
    p = PRICES[provider]
    return (in_tok * p["input"] + out_tok * p["output"]) / 1_000_000


def run_anthropic() -> None:
    import anthropic

    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    messages = [{"role": "user", "content": PROMPT}]

    # Pre-flight: ask the API exactly how many input tokens this will be.
    pre = client.messages.count_tokens(model=model, messages=messages)
    print(f"pre-flight input tokens: {pre.input_tokens}")

    resp = client.messages.create(model=model, max_tokens=1024, messages=messages)
    u = resp.usage  # real usage, billed
    print(f"actual: in={u.input_tokens} out={u.output_tokens}")
    print(f"estimated cost: ${dollars('anthropic', u.input_tokens, u.output_tokens):.6f}")


def run_openai() -> None:
    from openai import OpenAI

    client = OpenAI()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # OpenAI has no token-counting endpoint. For a true pre-flight count you'd use
    # `tiktoken` locally. Here we just read usage off the response after the call.
    resp = client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": PROMPT}]
    )
    u = resp.usage
    print(f"actual: in={u.prompt_tokens} out={u.completion_tokens}")
    print(f"estimated cost: ${dollars('openai', u.prompt_tokens, u.completion_tokens):.6f}")


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for name, fn in {"anthropic": run_anthropic, "openai": run_openai}.items():
        if which in (name, "both"):
            print(f"\n=== {name} ===")
            try:
                fn()
            except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
                print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
