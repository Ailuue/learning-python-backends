# Embeddings

## What is this?

An **embedding** turns a piece of text into a list of numbers (a vector) that
captures its *meaning*. Texts with similar meaning get vectors that point in
similar directions — even if they share no words. "How do I reset my password?"
and "I forgot my login credentials" land close together; "password" and
"passport" land far apart despite looking alike.

That single property — *meaning becomes geometry* — is what powers semantic
search, recommendations, clustering, deduplication, and the retrieval half of RAG
([../rag/](../rag/)).

## ⚠️ Anthropic has no embeddings API

This is the one place the "both providers side by side" pattern breaks, and it's
worth knowing: **Anthropic does not offer a first-party embeddings endpoint.**
Their docs recommend a third party, **[Voyage AI](https://www.voyageai.com/)**, for
embeddings. OpenAI *does* have its own (`text-embedding-3-*`).

So these examples pair **OpenAI** and **Voyage** rather than OpenAI and Anthropic.
The takeaway for a Claude-based stack: use Claude for generation, and Voyage (or
OpenAI, or an open model) for embeddings — they're separate concerns and you mix
and match.

## How similarity is measured

Compare two vectors with **cosine similarity** — the cosine of the angle between
them, from -1 (opposite) to 1 (identical direction). Closer to 1 = more similar in
meaning. These files compute it in plain Python so the math is visible (no numpy):

```
cos(a, b) = dot(a, b) / (||a|| * ||b||)
```

## ⚠️ Cosine scores aren't comparable across models

A raw cosine number only means something *within one model*. Each embedding model
packs its vectors into its own range, so the same pair scores very differently
depending on who embedded it. Running `01_generate_embeddings.py both` on the
identical sentences:

| | paraphrase (similar) | unrelated | separation |
|---|---|---|---|
| OpenAI `text-embedding-3-small` | 0.563 | 0.028 | 0.535 |
| Voyage `voyage-3` | 0.761 | 0.537 | 0.224 |

Voyage scoring the *unrelated* pair at 0.54 isn't "worse" than OpenAI's 0.03 — it's
just that Voyage's similarities sit in a high, narrow band while OpenAI spreads them
toward zero. Same meaning, different scale. Two rules follow:

- **Never hardcode a cross-model threshold.** "≥ 0.5 means relevant" is reasonable
  for OpenAI but would mark *everything* relevant for Voyage. Calibrate per model.
- **Don't judge model quality from absolute scores.** What matters is that the
  relevant item *ranks above* the irrelevant one — both models get that right — plus
  how the model does on retrieval benchmarks (e.g. MTEB), not whether its numbers
  look "high" or "low". `voyage-3` benchmarks competitively with, and often above,
  OpenAI's `text-embedding-3`.

## What the files cover

| File | What it teaches |
|---|---|
| `01_generate_embeddings.py` | Turn text into a vector with OpenAI and Voyage; see the dimensions and that similar sentences score higher |
| `02_semantic_search.py` | Embed a small corpus once, embed a query, rank by cosine similarity — semantic search that ignores exact wording |

## Where this connects

- The retrieval step in [../rag/](../rag/) is exactly `02_semantic_search.py` at
  scale, backed by a vector database.
- This repo already has a real vector store: the
  [pgvector demo](../../database-concepts/pgvector-demo/) stores embeddings in
  Postgres. Embeddings here + pgvector there = production semantic search.

## How to run

```bash
# Needs VOYAGE_API_KEY (free tier). OPENAI_API_KEY is optional — only for the OpenAI side.
python 01_generate_embeddings.py          # defaults to Voyage (free)
python 02_semantic_search.py both         # add OpenAI too (needs OpenAI credit)
```
