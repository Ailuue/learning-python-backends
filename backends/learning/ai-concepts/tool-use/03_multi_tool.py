"""Multiple tools: the model chooses which (and how many) to call.

Run: `python 03_multi_tool.py [anthropic|openai]`

Give the model a small toolbox — `get_weather`, `convert_currency` — and a
question that needs both. The model decides which tools are relevant and calls
them (often both in a single turn). Your loop doesn't change; it just dispatches
by name from a registry. That's how you scale from one tool to twenty: add to the
registry and the schema list, leave the loop alone.
"""
import json
import os
import sys
from typing import Any, cast

from dotenv import load_dotenv

load_dotenv()


def get_weather(city: str) -> str:
    return {"Tokyo": "22°C, humid", "Paris": "14°C, rain"}.get(city, "unknown")


def convert_currency(amount: float, from_ccy: str, to_ccy: str) -> str:
    rates = {("USD", "JPY"): 157.0, ("USD", "EUR"): 0.92}
    rate = rates.get((from_ccy, to_ccy))
    return "unknown" if rate is None else f"{amount * rate:.2f} {to_ccy}"


TOOLS = {"get_weather": get_weather, "convert_currency": convert_currency}

# One schema entry per tool. Provider wrappers below reshape these.
SCHEMAS = [
    {
        "name": "get_weather",
        "description": "Current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "convert_currency",
        "description": "Convert an amount between two ISO currency codes.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "from_ccy": {"type": "string"},
                "to_ccy": {"type": "string"},
            },
            "required": ["amount", "from_ccy", "to_ccy"],
        },
    },
]
QUESTION = "What's the weather in Tokyo, and how much is 50 USD in JPY?"


def run_anthropic() -> None:
    import anthropic
    from anthropic.types import MessageParam, ToolParam, ToolResultBlockParam

    client = anthropic.Anthropic()
    model = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
    tools: list[ToolParam] = [{"name": s["name"], "description": s["description"], "input_schema": s["parameters"]} for s in SCHEMAS]
    messages: list[MessageParam] = [{"role": "user", "content": QUESTION}]

    while True:
        r = client.messages.create(model=model, max_tokens=1024, tools=tools, messages=messages)
        if r.stop_reason != "tool_use":
            print("final:", "".join(b.text for b in r.content if b.type == "text"))
            return
        messages.append({"role": "assistant", "content": r.content})
        results: list[ToolResultBlockParam] = []
        for block in r.content:
            if block.type == "tool_use":
                print(f"  call: {block.name}({block.input})")
                results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": TOOLS[block.name](**cast(dict[str, Any], block.input))}
                )
        messages.append({"role": "user", "content": results})


def run_openai() -> None:
    from openai import OpenAI
    from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolUnionParam

    client = OpenAI()
    model = os.environ.get("OPENAI_MODEL", "gpt-4o")
    # SCHEMAS is a plain list of dicts, so the comprehension can't infer the
    # per-variant TypedDict — assert the shape the wrapper is building.
    tools = [
        cast(ChatCompletionToolUnionParam, {"type": "function", "function": s}) for s in SCHEMAS
    ]
    messages: list[ChatCompletionMessageParam] = [{"role": "user", "content": QUESTION}]

    while True:
        r = client.chat.completions.create(model=model, tools=tools, messages=messages)
        msg = r.choices[0].message
        if not msg.tool_calls:
            print("final:", msg.content)
            return
        # The SDK accepts its own response model here, but the parameter is
        # typed as a TypedDict — cast rather than reshape it.
        messages.append(cast(ChatCompletionMessageParam, msg))
        for tc in msg.tool_calls or []:
            if tc.type != "function":
                continue  # these demos only register function tools
            args = json.loads(tc.function.arguments)
            print(f"  call: {tc.function.name}({args})")
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": TOOLS[tc.function.name](**args)}
            )


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
