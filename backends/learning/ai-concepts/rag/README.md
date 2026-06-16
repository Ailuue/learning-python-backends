# RAG (Retrieval-Augmented Generation)

## What is this?

A model only knows what was in its training data. It doesn't know *your* docs,
*your* database, or anything that happened after its cutoff — and when asked
anyway, it often makes something up. **RAG** fixes this by *retrieving* relevant
text first and *augmenting* the prompt with it, so the model answers from real
information you supplied instead of from memory.

It's the single most common pattern for putting an LLM on top of a company's own
knowledge — support docs, internal wikis, product manuals, a user's files.

## The pipeline

```
        ┌─────────────── one-time indexing ───────────────┐
docs →  chunk  →  embed each chunk  →  store vectors in a DB
        └──────────────────────────────────────────────────┘

        ┌──────────────── per question ────────────────────┐
query → embed → find nearest chunks → stuff them into the
        prompt → model generates a grounded answer
        └──────────────────────────────────────────────────┘
```

Each piece you've already met:
- **chunk** — split documents into retrievable pieces ([01](01_chunking.py)).
- **embed / retrieve** — turn text into vectors and find the closest ones
  ([../embeddings/](../embeddings/)).
- **augment / generate** — build a prompt with the retrieved context and call the
  model ([../llm-api-basics/](../llm-api-basics/), [../prompt-engineering/](../prompt-engineering/)).

[02](02_pipeline.py) wires all of it into one end-to-end example.

## Why chunk at all?

You can't embed a 50-page document as one vector — it'd be a blurry average of
everything, and you'd feed the whole thing into every prompt (expensive, and it
buries the relevant part). Chunking lets you retrieve *just* the paragraph that
answers the question. Overlap between chunks avoids cutting a key sentence in half.

## RAG vs fine-tuning

When the model's gap is *knowledge*, RAG beats fine-tuning
([../prompt-engineering/04_fine_tuning_notes.md](../prompt-engineering/04_fine_tuning_notes.md)):
you can add, update, or delete a document and the next query reflects it
instantly, with no retraining. Fine-tuning bakes knowledge into frozen weights.

## What the files cover

| File | What it teaches |
|---|---|
| `01_chunking.py` | Splitting a document into overlapping chunks (no API calls — pure text handling) |
| `02_pipeline.py` | The full loop: index a tiny corpus, retrieve for a query, generate a grounded answer with Claude *and* GPT — and refuse to answer when the context doesn't contain it |

## What you need

- `VOYAGE_API_KEY` for embeddings (retrieval) — Voyage's free tier covers everything here.
- `ANTHROPIC_API_KEY` for the Claude generation side.
- `OPENAI_API_KEY` is **optional** — only for the OpenAI generation side. Without it,
  that half prints a `[skipped]` line and the pipeline still runs end to end.
- In production, swap the in-memory vector list for the
  [pgvector demo](../../database-concepts/pgvector-demo/) (🐘 Postgres).

## How to run

```bash
python 01_chunking.py
python 02_pipeline.py            # generates with both providers
python 02_pipeline.py anthropic
```
