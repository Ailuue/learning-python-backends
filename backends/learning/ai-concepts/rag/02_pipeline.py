"""End-to-end RAG: retrieve relevant context, then generate a grounded answer.

Run: `python 02_pipeline.py [anthropic|openai]`

The full loop:
  1. INDEX  — embed each document chunk (Voyage embeddings, free tier) and keep them.
  2. RETRIEVE — embed the question, score every chunk by cosine similarity, take
     the top few.
  3. AUGMENT — build a prompt containing ONLY those chunks as context, with a rule:
     answer from the context, and say "I don't know" if it isn't there.
  4. GENERATE — call the model (Claude and/or GPT) to write the answer.

The question asks about a company-specific policy the model was never trained on.
Without retrieval it would guess; with retrieval it answers correctly — and for a
question outside the context, the "I don't know" rule curbs hallucination.
"""
import math
import os
import sys

from dotenv import load_dotenv

load_dotenv()

KNOWLEDGE_BASE = [
    "Acme Cloud's free tier includes 5 GB of storage and 100 GB of monthly bandwidth.",
    "Acme Cloud paid plans start at $12/month for the Pro tier with 1 TB of storage.",
    "Support response time is under 4 hours for Pro customers and 24 hours on free.",
    "Acme Cloud stores all data encrypted at rest using AES-256.",
    "The Acme Cloud API is rate limited to 600 requests per minute per account.",
]
QUESTION = "What's the API rate limit, and how much storage does the free tier give me?"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm


def embed(texts: list[str]) -> list[list[float]]:
    # Retrieval uses Voyage (Anthropic-recommended embeddings, generous free tier),
    # so the whole pipeline runs without an OpenAI key. Swap to OpenAI's
    # client.embeddings.create if you prefer — the pipeline is identical either way.
    import voyageai

    vo = voyageai.Client()  # reads VOYAGE_API_KEY
    return vo.embed(
        texts, model=os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3"), input_type="document"
    ).embeddings


def retrieve(question: str, k: int = 2) -> list[str]:
    vectors = embed(KNOWLEDGE_BASE + [question])
    *doc_vecs, q_vec = vectors
    scored = sorted(zip((cosine(q_vec, d) for d in doc_vecs), KNOWLEDGE_BASE), reverse=True)
    return [doc for _, doc in scored[:k]]


def build_prompt(question: str, context: list[str]) -> str:
    joined = "\n".join(f"- {c}" for c in context)
    return (
        "Answer the question using ONLY the context below. "
        'If the answer is not in the context, say "I don\'t know".\n\n'
        f"Context:\n{joined}\n\nQuestion: {question}"
    )


def generate(provider: str, prompt: str) -> str:
    if provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic()
        r = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8"),
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in r.content if b.type == "text").strip()

    from openai import OpenAI

    client = OpenAI()
    r = client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return r.choices[0].message.content.strip()


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "both"

    try:
        context = retrieve(QUESTION, k=2)  # Voyage embeddings — provider-independent
    except Exception as e:  # e.g. missing Voyage key
        print(f"[retrieval skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")
        return
    print("retrieved context:")
    for c in context:
        print("  -", c)
    prompt = build_prompt(QUESTION, context)

    for provider in ("anthropic", "openai"):
        if which in (provider, "both"):
            print(f"\n=== {provider} ===")
            try:
                print(generate(provider, prompt))
            except Exception as e:  # e.g. unfunded key -> 429 insufficient_quota
                print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
