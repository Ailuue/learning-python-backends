"""Chain-of-thought: make the model reason before it answers.

Run: `python 02_chain_of_thought.py [anthropic|openai]`

We ask a small multi-step word problem two ways:
  - "answer only" — the model blurts a number and often gets it wrong.
  - "think step by step, then give the answer on a final line" — it works through
    the steps and lands the right number far more often.

CoT trades tokens and latency for accuracy. Use it when correctness on reasoning
matters more than speed. (Newer "reasoning" models do this internally; CoT
prompting is how you get the same effect from a standard chat model.)
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROBLEM = (
    "A server handles 1,200 requests/minute. 35% are cache hits taking 2ms each; "
    "the rest miss and take 50ms each. What is the average response time in ms? "
)

ANSWER_ONLY = PROBLEM + "Respond with only the number."
COT = PROBLEM + "Think step by step. Put the final number on its own last line prefixed with 'ANSWER: '."


def chat(provider: str, user: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=1024,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in r.content if b.type == "text").strip()

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=1024,
        messages=[{"role": "user", "content": user}],
    )
    content = r.choices[0].message.content
    if content is None:
        raise RuntimeError("model returned no text content")
    return content.strip()


def main() -> None:
    # Correct answer: 0.35*2 + 0.65*50 = 0.7 + 32.5 = 33.2 ms
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for provider in ("anthropic", "openai"):
        if which not in (provider, "both"):
            continue
        print(f"\n=== {provider} ===  (correct answer: 33.2)")
        try:
            print("  answer-only :", chat(provider, ANSWER_ONLY))
            cot = chat(provider, COT)
            # The reasoning is useful to read, but a program only wants the final line.
            final = cot.splitlines()[-1]
            print("  chain-of-thought final line:", final)
        except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
