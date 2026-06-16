# Fine-tuning — notes, not code

This file is deliberately prose-only. Fine-tuning is expensive, provider-specific,
and — for the large majority of backend use cases — **the wrong first tool**. The
goal here is to know what it is and, more importantly, when *not* to reach for it.

## What fine-tuning actually is

You take a base model and continue training it on your own labeled examples
(input → desired output), producing a new model snapshot that you then call by ID.
It adjusts the model's weights toward your data. It is *not* a way to give the
model new facts to look up — that's what RAG ([../rag/](../rag/)) is for.

## The cost reality

- **Money:** you pay to run the training job, then a higher per-token price to run
  inference on the resulting custom model.
- **Data:** you need hundreds to thousands of high-quality labeled examples.
  Gathering and cleaning them is the real cost, and it's mostly human time.
- **Maintenance:** the base model moves on. Your fine-tune is frozen against an
  older one, and re-tuning on each new base model is recurring work.

## The decision order (try these first)

For almost every problem, work down this list and stop at the first thing that
works:

1. **Better prompting** — few-shot examples and clear instructions
   ([01](01_zero_vs_few_shot.py), [03](03_prompt_templates.py)) solve a startling
   amount. Cheapest, fastest to iterate.
2. **RAG** — if the gap is *knowledge* ("the model doesn't know our docs / our
   data"), retrieval beats fine-tuning. You can update the knowledge base
   instantly; a fine-tune would need re-training. See [../rag/](../rag/).
3. **Tool use** — if the gap is *capability* ("it needs to look something up or
   take an action"), give it a tool ([../tool-use/](../tool-use/)).
4. **Fine-tuning** — only after the above fall short.

## When fine-tuning genuinely wins

- **Consistent style/format at scale** that's hard to specify but easy to
  demonstrate, where you don't want to spend tokens on few-shot examples in every
  call (fine-tuning bakes the pattern into the weights).
- **A narrow, high-volume task** where a smaller fine-tuned model can match a
  larger prompted one at much lower per-call cost and latency.
- **Latency/cost pressure** where trimming the long few-shot prompt out of every
  request pays for the training.

A useful tell: if your "instruction" is really *"do it like these 500 examples,"*
that's a fine-tuning shape. If it's *"use this information,"* that's RAG.

## Provider notes (high level)

- **OpenAI** offers a fine-tuning API: upload a JSONL file of example
  conversations, start a job, then call the returned model ID. This is the more
  common path in tutorials.
- **Anthropic** does not offer general open self-serve fine-tuning of Claude the
  same way; customization is typically handled through prompting, tools, and
  (for enterprise) managed offerings. **Default to prompting + RAG with Claude.**

Because the APIs, pricing, and data formats here change frequently and a real
training run costs real money, this module stops at the concepts. If you reach a
point where steps 1-3 above genuinely aren't enough, read the current provider
docs and budget for the data-labeling effort first — that, not the API call, is
the hard part.
