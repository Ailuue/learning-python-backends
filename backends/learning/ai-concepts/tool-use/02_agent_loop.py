"""The agent loop: keep calling tools until the model is done.

Run: `python 02_agent_loop.py [anthropic|openai]`

01 did a single round trip. Real tasks need several: the model calls a tool, sees
the result, decides it needs another, and so on. The `while` loop here keeps going
until the model stops asking for tools and produces a final answer.

The question ("How many more people live in Japan than Canada?") forces at least
two `get_population` calls, so you can watch the loop iterate. This loop, with a
richer tool set, is exactly what a coding agent or a research agent runs.
"""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# --- The tools, as plain Python. Shared by both providers. -------------------
_POP = {"Japan": 124_000_000, "Canada": 39_000_000, "Brazil": 203_000_000}


def get_population(country: str) -> str:
    return str(_POP.get(country, "unknown"))


TOOLS = {"get_population": get_population}

# JSON Schema for the arguments — identical content, wrapped differently per SDK.
_SCHEMA = {
    "type": "object",
    "properties": {"country": {"type": "string"}},
    "required": ["country"],
}
QUESTION = "How many more people live in Japan than Canada? Show the final number."


def run_anthropic() -> None:
    import anthropic

    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    tools = [{"name": "get_population", "description": "Population of a country.", "input_schema": _SCHEMA}]
    messages = [{"role": "user", "content": QUESTION}]

    while True:
        r = client.messages.create(model=model, max_tokens=1024, tools=tools, messages=messages)
        if r.stop_reason != "tool_use":
            print("final:", "".join(b.text for b in r.content if b.type == "text"))
            return

        messages.append({"role": "assistant", "content": r.content})
        results = []
        for block in r.content:
            if block.type == "tool_use":
                print(f"  call: {block.name}({block.input})")
                output = TOOLS[block.name](**block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})


def run_openai() -> None:
    from openai import OpenAI

    client = OpenAI()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    tools = [
        {
            "type": "function",
            "function": {"name": "get_population", "description": "Population of a country.", "parameters": _SCHEMA},
        }
    ]
    messages = [{"role": "user", "content": QUESTION}]

    while True:
        r = client.chat.completions.create(model=model, tools=tools, messages=messages)
        msg = r.choices[0].message
        if not msg.tool_calls:
            print("final:", msg.content)
            return

        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            print(f"  call: {tc.function.name}({args})")
            output = TOOLS[tc.function.name](**args)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})


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
