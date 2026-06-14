"""
In-memory data store for section 02.

Deliberately separate from schema.py so the N+1 counter is easy to observe.
"""

from dataclasses import dataclass


@dataclass
class Author:
    id: str
    name: str
    bio: str


@dataclass
class Post:
    id: str
    title: str
    body: str
    author_id: str


_SEED_AUTHORS = [
    {"id": "a1", "name": "Alice Nguyen",   "bio": "Distributed systems engineer"},
    {"id": "a2", "name": "Bob Okafor",     "bio": "Frontend performance specialist"},
    {"id": "a3", "name": "Carol Petersen", "bio": "Database architect"},
]

_SEED_POSTS = [
    {"id": "p1", "title": "Intro to CRDT",         "body": "CRDTs allow...", "author_id": "a1"},
    {"id": "p2", "title": "Raft Consensus",         "body": "Raft is...",    "author_id": "a1"},
    {"id": "p3", "title": "Core Web Vitals",        "body": "LCP, FID...",   "author_id": "a2"},
    {"id": "p4", "title": "CSS Grid Deep Dive",     "body": "Grid is...",    "author_id": "a2"},
    {"id": "p5", "title": "EXPLAIN ANALYZE",        "body": "Postgres...",   "author_id": "a3"},
    {"id": "p6", "title": "Index Selectivity",      "body": "Selectivity...", "author_id": "a3"},
]

authors: list[dict] = []
posts: list[dict] = []

# Tracks DB calls so tests can assert N+1 behaviour
class QueryCounter:
    calls: int = 0

    @classmethod
    def reset(cls) -> None:
        cls.calls = 0

    @classmethod
    def record(cls, label: str) -> None:
        cls.calls += 1


def reset() -> None:
    global authors, posts
    authors = [r.copy() for r in _SEED_AUTHORS]
    posts   = [r.copy() for r in _SEED_POSTS]
    QueryCounter.reset()


def get_author(author_id: str) -> dict | None:
    QueryCounter.record(f"get_author({author_id})")
    return next((a for a in authors if a["id"] == author_id), None)


def get_posts_by_author(author_id: str) -> list[dict]:
    QueryCounter.record(f"get_posts_by_author({author_id})")
    return [p for p in posts if p["author_id"] == author_id]


reset()
