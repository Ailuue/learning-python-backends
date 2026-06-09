"""
06 · Pagination — Offset and Cursor
=====================================

Two pagination styles demonstrated on the same 100-post dataset:
  A. Offset pagination  — simple, but inconsistent with concurrent mutations
  B. Cursor pagination  — stable pages even when items are added/removed

Strawberry provides `strawberry.relay` with built-in Relay Connection types.
This section shows the manual implementation first (so the concepts are clear),
then shows the Relay Connection type for reference.
"""

import strawberry
from typing import Optional

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data_06 as db


# ── Post type ─────────────────────────────────────────────────────────────────

@strawberry.type
class Post:
    id: strawberry.ID
    title: str
    body: str
    tags: list[str]


def _row_to_post(row: dict) -> Post:
    return Post(**row)


# ── Pattern A: Offset pagination ──────────────────────────────────────────────
#
# Clients pass offset (how many to skip) and limit (how many to return).
# Server returns a page + total count so clients can compute page numbers.

@strawberry.type
class PostPage:
    items: list[Post]
    total: int
    has_next_page: bool
    has_prev_page: bool


# ── Pattern B: Cursor pagination ──────────────────────────────────────────────
#
# Relay Connection specification:
#   - Each edge wraps a node with a cursor (opaque string, base64-encoded position)
#   - PageInfo tells clients if more pages exist and what cursor to use next
#   - `first` + `after` for forward pagination
#   - `last` + `before` for backward pagination
#
# Cursors are opaque to clients — they should not be parsed or constructed.
# Internally, the cursor encodes the item's stable identifier.

@strawberry.type
class PageInfo:
    has_next_page: bool
    has_prev_page: bool
    start_cursor: Optional[str] = None  # cursor of the first edge
    end_cursor: Optional[str] = None    # cursor of the last edge


@strawberry.type
class PostEdge:
    node: Post
    cursor: str   # opaque base64 string


@strawberry.type
class PostConnection:
    edges: list[PostEdge]
    page_info: PageInfo
    total_count: int


# ── Query ─────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    # Pattern A: offset pagination
    @strawberry.field
    def posts_page(
        self,
        offset: int = 0,
        limit: int = 10,
    ) -> PostPage:
        total = len(db.posts)
        page = db.posts[offset : offset + limit]
        return PostPage(
            items=[_row_to_post(p) for p in page],
            total=total,
            has_next_page=(offset + limit) < total,
            has_prev_page=offset > 0,
        )

    # Pattern B: cursor pagination (Relay Connection style)
    @strawberry.field
    def posts_connection(
        self,
        first: Optional[int] = 10,
        after: Optional[str] = None,
    ) -> PostConnection:
        all_posts = db.posts
        total = len(all_posts)

        # Find the starting position from the cursor
        start_index = 0
        if after is not None:
            after_id = db.decode_cursor(after)
            for i, p in enumerate(all_posts):
                if p["id"] == after_id:
                    start_index = i + 1
                    break

        page_size = first or 10
        page = all_posts[start_index : start_index + page_size]

        edges = [
            PostEdge(
                node=_row_to_post(p),
                cursor=db.encode_cursor(p["id"]),
            )
            for p in page
        ]

        return PostConnection(
            edges=edges,
            total_count=total,
            page_info=PageInfo(
                has_next_page=(start_index + page_size) < total,
                has_prev_page=start_index > 0,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
            ),
        )


schema = strawberry.Schema(query=Query)
