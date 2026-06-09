"""
Same data as section 02, with a batch-aware query function added.
"""

_SEED_AUTHORS = [
    {"id": "a1", "name": "Alice Nguyen",   "bio": "Distributed systems engineer"},
    {"id": "a2", "name": "Bob Okafor",     "bio": "Frontend performance specialist"},
    {"id": "a3", "name": "Carol Petersen", "bio": "Database architect"},
]

_SEED_POSTS = [
    {"id": "p1", "title": "Intro to CRDT",     "body": "CRDTs allow...", "author_id": "a1"},
    {"id": "p2", "title": "Raft Consensus",     "body": "Raft is...",    "author_id": "a1"},
    {"id": "p3", "title": "Core Web Vitals",    "body": "LCP, FID...",   "author_id": "a2"},
    {"id": "p4", "title": "CSS Grid Deep Dive", "body": "Grid is...",    "author_id": "a2"},
    {"id": "p5", "title": "EXPLAIN ANALYZE",    "body": "Postgres...",   "author_id": "a3"},
    {"id": "p6", "title": "Index Selectivity",  "body": "Selectivity...", "author_id": "a3"},
]

authors: list[dict] = []
posts: list[dict] = []


class BatchCounter:
    """Counts batch load calls (not individual item lookups)."""
    calls: int = 0

    @classmethod
    def reset(cls) -> None:
        cls.calls = 0


def reset() -> None:
    global authors, posts
    authors = [r.copy() for r in _SEED_AUTHORS]
    posts   = [r.copy() for r in _SEED_POSTS]
    BatchCounter.reset()


def get_authors_by_ids(ids: list[str]) -> list[dict | None]:
    """Batch load — returns one item per input id (None if not found)."""
    BatchCounter.calls += 1
    index = {a["id"]: a for a in authors}
    return [index.get(id) for id in ids]


reset()
