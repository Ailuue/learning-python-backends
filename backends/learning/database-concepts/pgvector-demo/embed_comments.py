"""
Embed all comments that don't yet have an embedding, using a local Ollama model.

Usage:
    python embed_comments.py                        # uses nomic-embed-text
    python embed_comments.py --model mxbai-embed-large

Before running:
    1. Install Ollama: https://ollama.com
    2. Pull the model:  ollama pull nomic-embed-text
    3. Ollama must be running (it starts automatically on macOS after install)
"""

import argparse
import sys

import ollama
from sqlalchemy import select

from database import get_session
from models import Comment

EMBEDDING_DIM = 768


def get_embedding(text: str, model: str) -> list[float]:
    response = ollama.embed(model=model, input=text)
    # ollama types embeddings as Sequence[float]; the column wants a list.
    vector = list(response.embeddings[0])
    if len(vector) != EMBEDDING_DIM:
        raise ValueError(
            f"Model '{model}' returned {len(vector)}-dim vectors, "
            f"but the embedding column expects {EMBEDDING_DIM}. "
            f"Update EMBEDDING_DIM in models.py and run a new migration."
        )
    return vector


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="nomic-embed-text", help="Ollama model to use")
    args = parser.parse_args()

    session = get_session()

    # Only fetch comments that haven't been embedded yet
    pending = session.scalars(
        select(Comment).where(Comment.embedding.is_(None))
    ).all()

    if not pending:
        print("All comments already have embeddings. Nothing to do.")
        session.close()
        return

    print(f"Embedding {len(pending)} comments with model '{args.model}'...")

    # Verify Ollama is reachable before processing the whole batch
    try:
        get_embedding(pending[0].body, args.model)
    except Exception as e:
        print(f"\nFailed to connect to Ollama or generate an embedding:\n  {e}")
        print("\nMake sure Ollama is installed and running, and that you've pulled the model:")
        print(f"  ollama pull {args.model}")
        sys.exit(1)

    for i, comment in enumerate(pending, start=1):
        vector = get_embedding(comment.body, args.model)
        comment.embedding = vector
        print(f"  [{i}/{len(pending)}] comment {comment.id}: {comment.body[:60]!r}")

    session.commit()
    session.close()
    print(f"\nDone. {len(pending)} comments embedded and saved to Postgres.")


if __name__ == "__main__":
    main()
