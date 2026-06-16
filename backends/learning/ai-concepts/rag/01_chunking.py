"""Chunking: split a document into overlapping pieces for retrieval.

Run: `python 01_chunking.py`  (no API calls — pure text handling)

Before you can embed and retrieve a document, you cut it into chunks small enough
to be specific but large enough to be self-contained. Overlap carries a little
context across the boundary so a sentence split between two chunks still appears
whole in at least one of them.

This is a simple character-based splitter. Real systems often split on sentence or
paragraph boundaries (or token counts), but the size/overlap trade-off is the same
idea everywhere.
"""

DOCUMENT = (
    "Our return policy allows refunds within 30 days of purchase. "
    "Items must be unused and in original packaging. "
    "Refunds are issued to the original payment method within 5 business days. "
    "Sale items are final and cannot be returned. "
    "To start a return, email support@example.com with your order number."
)


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Slide a window of `size` characters across the text, stepping by
    `size - overlap` so consecutive chunks share `overlap` characters."""
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    step = size - overlap
    return [text[i : i + size] for i in range(0, len(text), step) if text[i : i + size]]


def main() -> None:
    chunks = chunk_text(DOCUMENT, size=120, overlap=30)
    print(f"document length: {len(DOCUMENT)} chars")
    print(f"produced {len(chunks)} chunks (size=120, overlap=30):\n")
    for i, c in enumerate(chunks):
        print(f"[{i}] {c!r}")
    print("\nNote how the start of each chunk repeats the tail of the previous one —")
    print("that overlap is what keeps a boundary-straddling sentence retrievable.")


if __name__ == "__main__":
    main()
