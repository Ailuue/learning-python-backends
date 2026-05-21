"""
Pagination demo — two strategies side by side.

  GET /articles/offset?page=1&limit=10
  GET /articles/cursor?cursor=<token>&limit=10

Run with:
  uvicorn main:app --reload
"""

import base64
import json
import math
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Article

app = FastAPI(title="Pagination Demo")


# ── Cursor helpers ─────────────────────────────────────────────────────────────
#
# A cursor is an opaque token the client passes back on the next request.
# Internally it encodes the position in the result set — here, the ID of
# the last item the client received.
#
# We base64-encode a small JSON payload so the token is opaque (the client
# shouldn't need to know or depend on the structure), and so we can extend
# it later (e.g. add a secondary sort key) without changing the API shape.

def encode_cursor(article_id: int) -> str:
    payload = json.dumps({"id": article_id}).encode()
    return base64.urlsafe_b64encode(payload).decode()


def decode_cursor(token: str) -> int:
    try:
        payload = base64.urlsafe_b64decode(token.encode())
        return json.loads(payload)["id"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cursor token.")


# ── Offset pagination ──────────────────────────────────────────────────────────
#
# The classic approach: skip (page-1)*limit rows, then take limit rows.
#
# Pros:  simple, supports jumping to any page, easy total_pages calculation.
# Cons:  if rows are inserted/deleted between requests, pages can shift —
#        the same row may appear twice or be skipped entirely.
#        Also gets slower as OFFSET grows: the DB must still scan and discard
#        all the skipped rows.

@app.get("/articles/offset")
def list_articles_offset(
    page: int = Query(default=1, ge=1, description="Page number, 1-indexed"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(Article))

    articles = db.scalars(
        select(Article)
        .order_by(Article.published_at.desc(), Article.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    total_pages = math.ceil(total / limit)

    return {
        "data": [
            {
                "id": a.id,
                "title": a.title,
                "author": a.author,
                "published_at": a.published_at,
                "view_count": a.view_count,
            }
            for a in articles
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total_items": total,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        },
    }


# ── Cursor pagination ──────────────────────────────────────────────────────────
#
# Instead of OFFSET, we remember *where we left off* using the last item's ID.
# Each page filters with WHERE id < :last_id, which uses the primary-key index
# and stays fast regardless of how deep into the list you are.
#
# Pros:  stable — inserts/deletes don't shift pages; fast at any depth.
# Cons:  no random access (can't jump to page 7); total count not included
#        because it's expensive and usually unnecessary for infinite-scroll UIs.
#
# The "fetch limit+1" trick: we ask for one extra row. If we get it, there
# is a next page and we use that extra row's ID as the next cursor (then
# drop it from the response). If we get ≤ limit rows, we're on the last page.

@app.get("/articles/cursor")
def list_articles_cursor(
    cursor: Optional[str] = Query(default=None, description="Cursor token from previous response"),
    limit: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    query = select(Article).order_by(Article.id.desc())

    if cursor is not None:
        last_id = decode_cursor(cursor)
        query = query.where(Article.id < last_id)

    # Fetch one extra to cheaply detect whether another page exists
    rows = db.scalars(query.limit(limit + 1)).all()

    has_more = len(rows) > limit
    articles = rows[:limit]

    next_cursor = encode_cursor(articles[-1].id) if has_more else None

    return {
        "data": [
            {
                "id": a.id,
                "title": a.title,
                "author": a.author,
                "published_at": a.published_at,
                "view_count": a.view_count,
            }
            for a in articles
        ],
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
    }
