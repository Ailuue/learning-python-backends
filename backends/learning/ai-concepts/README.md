# AI Engineering

The skills a backend engineer now needs to wire LLMs into a service: calling the
APIs, shaping prompts, forcing structured output, giving the model tools, and
building retrieval (RAG) and evaluation around it.

Every runnable example shows **two providers side by side** — Anthropic (Claude)
and OpenAI (GPT) — usually as two functions in the same file so you can read the
same idea against both SDKs. The patterns are the lesson; the SDK is an
implementation detail you can swap.

## ⚠️ These cost real money

Unlike the Redis/Postgres modules, there's no `docker run` — every script hits a
paid API. Costs are small (cents) but real. To keep spend low while learning, set
the cheap models in your `.env` (see [.env.example](.env.example)):

```
ANTHROPIC_MODEL=claude-haiku-4-5
OPENAI_MODEL=gpt-4o-mini
```

## Modules

Work the **core path** in order — each builds on the last. The **specialized**
topics can be done in any order afterward.

### Core path — do these in order

| # | Folder | Topics | Needs |
|---|---|---|---|
| 1 | [llm-api-basics/](llm-api-basics/) | Messages/chat API, system vs user roles, streaming, token counting & cost | ☁️ |
| 2 | [prompt-engineering/](prompt-engineering/) | Zero/few-shot, chain-of-thought, prompt templates; when to fine-tune (and when not to) | ☁️ |
| 3 | [structured-outputs/](structured-outputs/) | Forcing JSON, validating with Pydantic, handling malformed output | ☁️ |
| 4 | [tool-use/](tool-use/) | Function/tool calling, the agent loop, multiple tools | ☁️ |

### Specialized topics — any order, after the core path

| Folder | Topics | Needs |
|---|---|---|
| [embeddings/](embeddings/) | Generating embeddings, semantic similarity, semantic search | ☁️ |
| [rag/](rag/) | Chunk → embed → retrieve → augment → generate, the full pipeline | ☁️🐘 |
| [evaluation/](evaluation/) | LLM-as-judge, building a small eval harness | ☁️ |
| [guardrails/](guardrails/) | Prompt-injection defense, input/output validation | ☁️ |

**Legend:** ☁️ external LLM API (costs money) · 🐘 PostgreSQL (RAG reuses the
[pgvector demo](../database-concepts/pgvector-demo/))

## Setup

```bash
cd ai-concepts
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your API keys
```

Each script is self-contained and runnable on its own:

```bash
python llm-api-basics/01_first_call.py
```

By default a script runs **both** providers. Pass a provider name to run just one:

```bash
python llm-api-basics/01_first_call.py anthropic
python llm-api-basics/01_first_call.py openai
```

If a provider's key is missing or unfunded, that provider prints a `[skipped — …]`
line and the script keeps going — one unfunded provider never crashes a run. And the
**embeddings/** and **rag/** modules default to **Voyage** (free tier) for embeddings,
so **OpenAI is optional** throughout: the whole module runs on a funded Anthropic key
plus the free Voyage tier.

## A note on the two providers

The **Anthropic** code in this module follows Anthropic's current SDK
conventions (the Messages API, `client.messages.parse()`, the manual tool loop).
The **OpenAI** code uses the Chat Completions API. They differ in spelling, not in
concept — both send a list of role-tagged messages and get back a completion.
Where a capability exists on one side and not the other (Anthropic has no
first-party **embeddings** endpoint — it recommends [Voyage AI](https://www.voyageai.com/)),
the README for that module says so instead of faking a symmetric example.

## Conventions

Same as the rest of [the learning repo](../README.md):

- **Folder names use hyphens.** Step files use a zero-padded number prefix
  (`01_first_call.py`) so reading order is obvious.
- **The "why" lives in each module's `README.md`;** code files carry short
  docstrings for the "what."
- One fine-tuning note ([prompt-engineering/04_fine_tuning_notes.md](prompt-engineering/04_fine_tuning_notes.md))
  is prose-only by design — fine-tuning is expensive and provider-specific, so it's
  documented rather than run.
