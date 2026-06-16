"""Turn text into vectors and measure meaning-similarity.

Run: `python 01_generate_embeddings.py [openai|voyage]`

We embed three sentences. Two mean the same thing in different words; the third is
unrelated. The cosine similarity between the two paraphrases should be clearly
higher than either's similarity to the unrelated one — meaning, not wording,
drives the score.

Remember: there's no Anthropic embeddings endpoint, so the two providers here are
OpenAI and Voyage AI (the embedder Anthropic recommends).
"""
import math
import os
import sys

from dotenv import load_dotenv

load_dotenv()

SENTENCES = [
    "How do I reset my password?",          # 0
    "I forgot my login credentials.",        # 1  (same meaning as 0)
    "The restaurant served great pasta.",    # 2  (unrelated)
]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm


def embed_openai(texts: list[str]) -> list[list[float]]:
    from openai import OpenAI

    client = OpenAI()
    resp = client.embeddings.create(
        model=os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        input=texts,
    )
    return [d.embedding for d in resp.data]


def embed_voyage(texts: list[str]) -> list[list[float]]:
    import voyageai

    vo = voyageai.Client()  # reads VOYAGE_API_KEY
    result = vo.embed(
        texts,
        model=os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3"),
        input_type="document",
    )
    return result.embeddings


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "voyage"  # Voyage is free; pass "both"/"openai" to include OpenAI
    for name, fn in {"openai": embed_openai, "voyage": embed_voyage}.items():
        if which not in (name, "both"):
            continue
        print(f"\n=== {name} ===")
        try:
            vecs = fn(SENTENCES)
            print(f"  vector dimensions: {len(vecs[0])}")
            print(f"  sim(0,1) paraphrase : {cosine(vecs[0], vecs[1]):.3f}")
            print(f"  sim(0,2) unrelated  : {cosine(vecs[0], vecs[2]):.3f}")
        except Exception as e:  # e.g. missing/unfunded key
            print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
