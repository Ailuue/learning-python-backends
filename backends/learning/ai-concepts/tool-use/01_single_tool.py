"""One tool, one round trip — the tool-use cycle spelled out by hand.

Run: `python 01_single_tool.py [anthropic|openai]`

The model can't know live weather, so we give it a `get_weather` tool. Watch the
cycle: we send the question + tool definition; the model asks us to call
`get_weather(city=...)`; OUR code runs the (mocked) function; we send the result
back; the model writes the final natural-language answer.

The model only ever *requests* the call. We execute it. That boundary is the whole
security story of tool use.
"""
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_weather(city: str) -> str:
    """Pretend this hits a real weather API. Returns a string the model can read."""
    fake = {"Lisbon": "19°C, clear", "Oslo": "3°C, snow"}
    return fake.get(city, "unknown")


QUESTION = "What's the weather in Lisbon? Reply in one sentence."


def run_anthropic() -> None:
    import anthropic

    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "input_schema": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
        }
    ]
    messages = [{"role": "user", "content": QUESTION}]
    r = client.messages.create(model=model, max_tokens=512, tools=tools, messages=messages)
    print("stop_reason:", r.stop_reason)  # -> "tool_use"

    # Echo the assistant's turn (including the tool_use block) back into history.
    messages.append({"role": "assistant", "content": r.content})

    results = []
    for block in r.content:
        if block.type == "tool_use":
            print(f"  model wants: {block.name}({block.input})")
            output = get_weather(**block.input)
            results.append(
                {"type": "tool_result", "tool_use_id": block.id, "content": output}
            )
    messages.append({"role": "user", "content": results})

    final = client.messages.create(model=model, max_tokens=512, tools=tools, messages=messages)
    print("final:", "".join(b.text for b in final.content if b.type == "text"))


def run_openai() -> None:
    from openai import OpenAI

    client = OpenAI()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "City name"}},
                    "required": ["city"],
                },
            },
        }
    ]
    messages = [{"role": "user", "content": QUESTION}]
    r = client.chat.completions.create(model=model, tools=tools, messages=messages)
    msg = r.choices[0].message
    print("finish_reason:", r.choices[0].finish_reason)  # -> "tool_calls"

    messages.append(msg)  # the assistant message, carrying tool_calls
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)
        print(f"  model wants: {tc.function.name}({args})")
        output = get_weather(**args)
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": output})

    final = client.chat.completions.create(model=model, tools=tools, messages=messages)
    print("final:", final.choices[0].message.content)


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
