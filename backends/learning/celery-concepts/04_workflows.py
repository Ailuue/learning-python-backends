"""
Concept 04 — Workflows: chain, group, chord

Celery lets you compose tasks into pipelines using three primitives:

  chain(a, b, c)
    ─────────────────────────────────────────────────────────────────
    Sequential pipeline. The return value of each task is passed as
    the *first argument* to the next task.

    a() → result_a → b(result_a) → result_b → c(result_b) → final

    Use for: ETL steps, multi-stage processing, ordered dependencies.

  group(a, b, c)
    ─────────────────────────────────────────────────────────────────
    Parallel fan-out. All tasks run concurrently. Returns a GroupResult
    you can call .get() on to collect all results as a list.

    a()  ─┐
    b()  ─┼─ [result_a, result_b, result_c]
    c()  ─┘

    Use for: independent parallel work (resize 5 images at once).

  chord(group, callback)
    ─────────────────────────────────────────────────────────────────
    Fan-out + fan-in. Runs a group in parallel, then calls the callback
    with a list of all results once every task in the group succeeds.

    a()  ─┐
    b()  ─┼─ [ra, rb, rc] → callback([ra, rb, rc]) → final
    c()  ─┘

    Use for: scatter-gather (map-reduce style).

Signatures (`.s()` and `.si()`):
  task.s(arg)   → "lazy call" — creates a Signature object (not yet run).
                  Passes the previous result as first arg (for chains).
  task.si(arg)  → "immutable signature" — ignores the previous result.
                  Use inside groups/chords where you don't want chain passing.

HOW TO RUN THIS FILE:
  Terminal 1:  docker compose up
  Terminal 2:  celery -A 04_workflows worker --loglevel=info --concurrency=4
  Terminal 3:  python 04_workflows.py
"""

import time
from celery import chain, group, chord
from celery_app import app


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@app.task
def download(url: str) -> dict:
    time.sleep(0.5)
    return {"url": url, "content": f"<html>{url}</html>", "size_kb": len(url) * 10}


@app.task
def parse(downloaded: dict) -> dict:
    """Receives the dict that download() returned (chain passes it automatically)."""
    content = downloaded["content"]
    return {"url": downloaded["url"], "words": len(content.split()), "size_kb": downloaded["size_kb"]}


@app.task
def store(parsed: dict) -> str:
    """Final step — persists the result."""
    return f"Stored: {parsed['url']} ({parsed['words']} words)"


@app.task
def resize_image(image_id: int, size: str) -> dict:
    time.sleep(0.3)
    return {"image_id": image_id, "size": size, "path": f"/img/{image_id}_{size}.jpg"}


@app.task
def aggregate_results(results: list) -> dict:
    """
    Chord callback — receives the list of results from the group.
    `results` is automatically filled in by Celery.
    """
    return {
        "total": len(results),
        "summary": [r["path"] for r in results],
    }


@app.task
def add(x, y):
    return x + y


@app.task
def multiply(x, y):
    return x * y


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CONCEPT 04 — Workflows (chain / group / chord)")
    print("=" * 60)

    # ── 1. chain ────────────────────────────────────────────────────────────
    print("\n1. chain — sequential pipeline (download → parse → store):")
    # .s() creates a Signature. Each task's return value feeds the next.
    pipeline = chain(
        download.s("https://example.com/page"),
        parse.s(),   # receives download()'s return value as first arg
        store.s(),   # receives parse()'s return value as first arg
    )
    result = pipeline.delay()
    output = result.get(timeout=15)
    print(f"   Result: {output}")

    # Shorthand using the | pipe operator (same as chain()):
    print("\n   (Same pipeline using | operator):")
    pipeline2 = download.s("https://example.com/other") | parse.s() | store.s()
    output2 = pipeline2.delay().get(timeout=15)
    print(f"   Result: {output2}")

    # ── 2. group ────────────────────────────────────────────────────────────
    print("\n2. group — parallel fan-out (resize one image in 3 sizes at once):")
    # .si() = immutable signature; we don't want the group to chain-pass anything
    parallel = group(
        resize_image.si(42, "small"),
        resize_image.si(42, "medium"),
        resize_image.si(42, "large"),
    )
    group_result = parallel.delay()
    outputs = group_result.get(timeout=15)
    for o in outputs:
        print(f"   {o}")

    # ── 3. chord ────────────────────────────────────────────────────────────
    print("\n3. chord — parallel fan-out + single callback (map-reduce):")
    image_ids = [10, 11, 12, 13]
    tasks = group(resize_image.si(img_id, "thumb") for img_id in image_ids)
    pipeline3 = chord(tasks, aggregate_results.s())
    result3 = pipeline3.delay()
    output3 = result3.get(timeout=20)
    print(f"   Aggregated: {output3}")

    # ── 4. chain of arithmetic (shows value passing clearly) ────────────────
    print("\n4. Arithmetic chain — result passing in action:")
    # add(1, 2) = 3  →  multiply(3, 10) = 30
    # Note: multiply.s(10) means multiply(prev_result, 10)
    math_chain = add.s(1, 2) | multiply.s(10)
    answer = math_chain.delay().get(timeout=10)
    print(f"   add(1,2)=3, then multiply(3,10) = {answer}")


if __name__ == "__main__":
    main()
