# LLM API Basics

## What is this?

Calling an LLM is, at the wire level, a boring HTTP POST: you send a list of
messages, you get back generated text. Everything fancy — agents, RAG,
chatbots — is built on this one primitive. This module is the primitive.

Both Anthropic and OpenAI model a request the same way: a list of messages, each
tagged with a **role**. The model reads the conversation so far and writes the
next assistant turn. The API is **stateless** — it remembers nothing between
calls, so *you* resend the whole conversation every time (you'll feel this in
[02](02_system_prompts.py) and again in tool use).

## The mental model

```
[system prompt]        ← who the model is, how it should behave (set by you)
[user message]         ← what the human said
[assistant message]    ← what the model said
[user message]         ← ... and so on. You resend this whole list each call.
```

## The two key roles

- **system** — instructions that frame the whole conversation ("You are a terse
  SQL assistant"). Anthropic takes this as a top-level `system=` parameter; OpenAI
  takes it as the first message with `role: "system"`. Same idea, different slot.
- **user** / **assistant** — the back-and-forth. The first message must be `user`.

## What the files cover

| File | What it teaches |
|---|---|
| `01_first_call.py` | The absolute minimum request against both providers; how to dig the text out of each response shape |
| `02_system_prompts.py` | Steering behavior with a system prompt; building a multi-turn conversation by hand (the API is stateless) |
| `03_streaming.py` | Streaming tokens as they're generated, so a UI isn't frozen for 10 seconds |
| `04_token_counting_cost.py` | Counting tokens *before* you send, and estimating what a call costs |

## Why this matters for backend work

- **Latency.** A non-streaming call blocks until the whole response is done.
  Streaming ([03](03_streaming.py)) is how you keep a request feeling responsive.
- **Cost.** You pay per token, in and out. Knowing how to count tokens
  ([04](04_token_counting_cost.py)) is the difference between a $5 feature and a
  $5,000 surprise.
- **Statelessness.** Because the server holds no memory, conversation history is
  *your* job — usually a database row, replayed into `messages` on every call.

## How to run

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # add your keys
python 01_first_call.py            # runs both providers
python 01_first_call.py anthropic  # or just one
```
