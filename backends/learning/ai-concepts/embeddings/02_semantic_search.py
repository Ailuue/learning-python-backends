"""Semantic search: rank a corpus by meaning, not keyword overlap.

Run: `python 02_semantic_search.py [openai|voyage]`

We embed a small "knowledge base" once, embed a query, and rank documents by
cosine similarity to the query. Note the winning document for "my card was
declined" shares almost no words with the query — keyword search would miss it;
semantic search finds it because the *meaning* matches.

This is the retrieval step of RAG, in miniature. At scale you'd store the document
vectors in a vector database (see ../../database-concepts/pgvector-demo/) instead
of a Python list, but the ranking idea is identical.
"""
import math
import os
import sys

from dotenv import load_dotenv

load_dotenv()

CORPUS = [
    "To return an item, visit your orders page and click 'Start a return'.",
    "Payment failures are usually caused by an expired or blocked card.",
    "Our office is open Monday to Friday, 9am to 5pm.",
    "You can change your notification settings under Account > Preferences.",
]
QUERY = "my card was declined at checkout"


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm


def embed(provider: str, texts: list[str]) -> list[list[float]]:
    if provider == "openai":
        from openai import OpenAI

        client = OpenAI()
        resp = client.embeddings.create(
            model=os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
            input=texts,
        )
        return [d.embedding for d in resp.data]

    import voyageai

    # voyageai ships no __all__, so pyright reads Client as a private import.
    vo = voyageai.Client()  # pyright: ignore[reportPrivateImportUsage]
    vectors = vo.embed(
        texts, model=os.environ.get("VOYAGE_EMBED_MODEL", "voyage-3"), input_type="document"
    ).embeddings
    # embeddings is List[List[float]] | List[List[int]] because voyage can return
    # int8 vectors; the default output dtype is float, which is what we ask for.
    return [[float(x) for x in vec] for vec in vectors]


def search(provider: str) -> None:
    # Embed corpus + query together, then score each doc against the query.
    vectors = embed(provider, CORPUS + [QUERY])
    *doc_vecs, query_vec = vectors

    ranked = sorted(
        ((cosine(query_vec, dv), doc) for dv, doc in zip(doc_vecs, CORPUS)),
        reverse=True,
    )
    print(f'  query: "{QUERY}"')
    for score, doc in ranked:
        print(f"    {score:.3f}  {doc}")


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else "voyage"  # Voyage is free; pass "both"/"openai" to include OpenAI
    for provider in ("openai", "voyage"):
        if which in (provider, "both"):
            print(f"\n=== {provider} ===")
            try:
                search(provider)
            except Exception as e:  # e.g. missing/unfunded key
                print(f"  [skipped — {type(e).__name__}: {str(e).splitlines()[0][:110]}]")


if __name__ == "__main__":
    main()
