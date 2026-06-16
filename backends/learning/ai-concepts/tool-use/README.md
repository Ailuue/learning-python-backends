# Tool Use (Function Calling)

## What is this?

By itself a model can only produce text from its training data. **Tool use** (aka
function calling) lets it ask *your* code to do things — look up a row, call an
API, run a calculation — and then use the result to keep going. This is the
mechanism behind every "agent": the model decides *what* to call, your code
actually calls it, and the model reads the result.

Crucially, **the model never runs your code.** It emits a structured request ("call
`get_weather` with `{city: 'Lisbon'}`"); your program executes the function and
feeds the return value back. You are always in control of what actually happens.

## The loop

This is the whole pattern — memorize it:

```
1. Send the user message + your tool definitions.
2. Model replies. Either:
     a. a normal answer  -> done.
     b. a tool-call request -> go to 3.
3. Run the requested function(s) in YOUR code.
4. Append the tool result(s) to the conversation, send again.
5. Back to 2. Repeat until the model gives a normal answer.
```

[02](02_agent_loop.py) implements exactly this as a `while` loop — that loop *is*
an agent.

## Anthropic vs OpenAI, same shape

Both define tools as name + description + a JSON Schema for the arguments, and
both return a structured tool-call request you must satisfy. The spellings differ:

| | Anthropic | OpenAI |
|---|---|---|
| Define | `tools=[{name, description, input_schema}]` | `tools=[{type:"function", function:{name, description, parameters}}]` |
| Model wants a tool | `stop_reason == "tool_use"`, `tool_use` blocks | `finish_reason == "tool_calls"`, `message.tool_calls` |
| Send result back | user message with `tool_result` block (`tool_use_id`) | message with `role:"tool"` (`tool_call_id`) |

## What the files cover

| File | What it teaches |
|---|---|
| `01_single_tool.py` | One tool, one round trip: see the request → execute → result → final answer cycle by hand |
| `02_agent_loop.py` | The general `while` loop that keeps going until the model is done — the core of an agent |
| `03_multi_tool.py` | Several tools; the model chooses which (and how many) to call |

## When would you use this?

Whenever the answer depends on something the model can't know or can't do: current
data, your database, a third-party API, an action with a side effect (send email,
create ticket). Tool use is also how RAG retrieval can be wired
([../rag/](../rag/)).

## How to run

```bash
python 01_single_tool.py
python 02_agent_loop.py openai
```
