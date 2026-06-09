"""
02 · Relationships & the N+1 Problem
=====================================

This schema demonstrates how related types work in GraphQL and
why naive resolver implementations cause the N+1 query problem.
"""

import strawberry
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data_02 as db


# ── Types ─────────────────────────────────────────────────────────────────────
#
# Post and Author each have a field that loads the other type.
# The resolver for that field is defined as a method on the class.
#
# strawberry.Private[T] marks a field as NOT exposed in the GraphQL schema.
# Use it to carry internal state (like author_id) through the type without
# exposing it to clients.

@strawberry.type
class Author:
    id: strawberry.ID
    name: str
    bio: str

    # This method is called once per Author instance when the client
    # requests the `posts` field. With 3 authors, that's 3 extra DB calls.
    @strawberry.field
    def posts(self) -> list["Post"]:
        rows = db.get_posts_by_author(str(self.id))
        return [_row_to_post(r) for r in rows]


@strawberry.type
class Post:
    id: strawberry.ID
    title: str
    body: str
    author_id: strawberry.Private[str]   # NOT in schema — internal only

    # Called once per Post instance when client requests `author`.
    # Querying 6 posts = 6 separate get_author calls (the N+1 problem).
    @strawberry.field
    def author(self) -> Optional[Author]:
        row = db.get_author(self.author_id)
        return _row_to_author(row) if row else None


def _row_to_author(row: dict) -> Author:
    return Author(id=row["id"], name=row["name"], bio=row["bio"])


def _row_to_post(row: dict) -> Post:
    return Post(id=row["id"], title=row["title"], body=row["body"], author_id=row["author_id"])


# ── Query ──────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field
    def posts(self) -> list[Post]:
        return [_row_to_post(p) for p in db.posts]

    @strawberry.field
    def post(self, id: strawberry.ID) -> Optional[Post]:
        row = next((p for p in db.posts if p["id"] == id), None)
        return _row_to_post(row) if row else None

    @strawberry.field
    def authors(self) -> list[Author]:
        return [_row_to_author(a) for a in db.authors]

    @strawberry.field
    def author(self, id: strawberry.ID) -> Optional[Author]:
        row = next((a for a in db.authors if a["id"] == id), None)
        return _row_to_author(row) if row else None


schema = strawberry.Schema(query=Query)
