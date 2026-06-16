# Structured Outputs

## What is this?

An LLM returns text. But your code needs *data* — a dict with known fields, not a
paragraph. Structured outputs are the techniques for making the model emit valid,
parseable JSON that matches a schema you define, so the next line of code can
`json.loads()` it without praying.

This is the bridge between "the model said something" and "my program can act on
it." It's what turns an LLM into a component you can put in a pipeline.

## The progression

**1. Just ask for JSON** ([01](01_json_mode.py)) — instruct the model to return
JSON and parse it. Works, but it's fragile: the model might wrap it in
```` ```json ```` fences, add a "Here you go:" preamble, or hallucinate a field.
You're parsing hope.

**2. Enforce a schema** ([02](02_pydantic_schema.py)) — give the API a schema
(via a Pydantic model) and let it *constrain generation* to match. The provider
guarantees the shape; you get back a validated object, not a string. This is the
production answer. Both Anthropic (`messages.parse`) and OpenAI
(`beta.chat.completions.parse`) support it with the same Pydantic model.

**3. Handle the failures that remain** ([03](03_handling_failures.py)) — even
with schema enforcement things go wrong: the model refuses, the output is
truncated at `max_tokens`, or a value is schema-valid but semantically wrong.
Defensive parsing and a retry loop.

## When would you use this?

Anywhere the LLM output feeds code rather than a human: extracting fields from an
email, classifying with metadata, generating an API request body, populating a
form. Basically every backend LLM feature.

## What the files cover

| File | What it teaches |
|---|---|
| `01_json_mode.py` | Asking for JSON and parsing it — and the failure modes that make this fragile |
| `02_pydantic_schema.py` | Defining a Pydantic model once and getting a validated object from both providers |
| `03_handling_failures.py` | Catching `ValidationError`, refusals, and truncation; a simple retry-on-invalid loop |

## How to run

```bash
python 01_json_mode.py
python 02_pydantic_schema.py anthropic
```
