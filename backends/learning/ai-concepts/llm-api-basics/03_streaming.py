"""Streaming: print tokens as they arrive instead of waiting for the whole reply.

Run: `python 03_streaming.py [anthropic|openai]`

Without streaming, the user stares at a frozen screen until the entire response is
generated — which can be many seconds for a long answer. Streaming delivers the
text token-by-token, so a UI (or a CLI like this one) can render it live. This is
the single biggest perceived-latency win in any LLM product.

Both SDKs expose streaming as an iterator of small chunks. The accumulation is
done for you by Anthropic's `.stream()` helper; OpenAI yields raw deltas.
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()

PROMPT = "Explain how a TCP handshake works, in about 4 sentences."


def stream_anthropic() -> None:
    import anthropic

    client = anthropic.Anthropic()
    with client.messages.stream(
        model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT}],
    ) as stream:
        for text in stream.text_stream:  # already-decoded text chunks
            print(text, end="", flush=True)
    print()


def stream_openai() -> None:
    from openai import OpenAI

    client = OpenAI()
    stream = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": PROMPT}],
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content  # may be None on the first/last chunk
        if delta:
            print(delta, end="", flush=True)
    print()


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    for name, fn in {"anthropic": stream_anthropic, "openai": stream_openai}.items():
        if which in (name, "both"):
            print(f"\n=== {name} ===")
            try:
                fn()
            except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
                print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
