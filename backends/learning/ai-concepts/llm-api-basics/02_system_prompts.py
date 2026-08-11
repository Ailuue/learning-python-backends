"""System prompts (steering behavior) and multi-turn conversations.

Run: `python 02_system_prompts.py [anthropic|openai]`

Two lessons here:
  1. The SAME user question gives very different answers depending on the system
     prompt. That's your main lever for controlling tone, format, and persona.
  2. The API is STATELESS. To have a "conversation", you keep a list of messages
     yourself and resend the whole thing each turn. Notice how the second call
     includes the first exchange — that's the only reason the model "remembers".
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

SYSTEM = "You are a grumpy senior engineer. Answer correctly but tersely, with a sigh."
TURN_1 = "What is a database index?"
TURN_2 = "Could it ever slow things down?"  # 'it' only makes sense if turn 1 is remembered


def run_anthropic() -> None:
    import anthropic
    from anthropic.types import MessageParam

    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")

    # Anthropic: system is a TOP-LEVEL parameter, not a message.
    # Annotate the history so appends below stay typed as MessageParam rather
    # than collapsing to dict[str, str].
    history: list[MessageParam] = [{"role": "user", "content": TURN_1}]
    r1 = client.messages.create(model=model, max_tokens=1024, system=SYSTEM, messages=history)
    a1 = "".join(b.text for b in r1.content if b.type == "text")
    print("A1:", a1)

    # Append the assistant's reply + the next user turn, then resend EVERYTHING.
    history.append({"role": "assistant", "content": a1})
    history.append({"role": "user", "content": TURN_2})
    r2 = client.messages.create(model=model, max_tokens=1024, system=SYSTEM, messages=history)
    print("A2:", "".join(b.text for b in r2.content if b.type == "text"))


def run_openai() -> None:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageParam

    client = OpenAI()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    # OpenAI: system is the FIRST message in the list (role="system").
    history: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": TURN_1},
    ]
    r1 = client.chat.completions.create(model=model, messages=history)
    a1 = r1.choices[0].message.content
    if a1 is None:
        raise RuntimeError("model returned no text content")
    print("A1:", a1)

    history.append({"role": "assistant", "content": a1})
    history.append({"role": "user", "content": TURN_2})
    r2 = client.chat.completions.create(model=model, messages=history)
    print("A2:", r2.choices[0].message.content)


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
