"""
03 · DataLoaders — solving N+1
===============================

Same schema as section 02, but Post.author now uses a DataLoader
from context instead of calling the DB directly.

When the GraphQL executor resolves a list of posts, all Post.author
resolvers are scheduled before any of them actually run. The DataLoader
accumulates all the author_id keys during that tick, then fires a single
batch query to fetch all of them at once.
"""

import strawberry
from strawberry.types import Info
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data_03 as db
from loaders_03 import make_author_loader


# ── Context ───────────────────────────────────────────────────────────────────
#
# Context is a per-request object passed to all resolvers via `info.context`.
# We use it to hold the DataLoader instance, which is created fresh each request.

@strawberry.type
class Context:
    author_loader: strawberry.Private[object]   # DataLoader instance


# ── Types ─────────────────────────────────────────────────────────────────────

@strawberry.type
class Author:
    id: strawberry.ID
    name: str
    bio: str


@strawberry.type
class Post:
    id: strawberry.ID
    title: str
    body: str
    author_id: strawberry.Private[str]

    @strawberry.field
    async def author(self, info: Info) -> Optional[Author]:
        # info.context.author_loader.load() schedules a key for batching.
        # All load() calls within one resolver tick are batched together.
        row = await info.context["author_loader"].load(self.author_id)
        if row is None:
            return None
        return Author(id=row["id"], name=row["name"], bio=row["bio"])


def _row_to_post(row: dict) -> Post:
    return Post(id=row["id"], title=row["title"], body=row["body"], author_id=row["author_id"])


# ── Query ─────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field
    def posts(self) -> list[Post]:
        return [_row_to_post(p) for p in db.posts]

    @strawberry.field
    def post(self, id: strawberry.ID) -> Optional[Post]:
        row = next((p for p in db.posts if p["id"] == id), None)
        return _row_to_post(row) if row else None


schema = strawberry.Schema(query=Query)


def make_context() -> dict:
    """Create a fresh context dict with a new DataLoader for each request."""
    return {"author_loader": make_author_loader()}
