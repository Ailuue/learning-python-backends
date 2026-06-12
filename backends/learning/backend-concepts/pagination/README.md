# Pagination

Two pagination strategies implemented side by side in a single FastAPI app.

## Strategies

### Offset Pagination
`GET /articles/offset?page=1&limit=10`

The client specifies a page number and page size. The database skips `(page - 1) * limit` rows and returns the next `limit`.

**When to use:** small datasets, admin UIs where jumping to page 50 is useful.

**Drawback:** if a new row is inserted while the user is browsing, items shift — causing duplicates or skipped rows between pages.

### Cursor Pagination
`GET /articles/cursor?cursor=<token>&limit=10`

The cursor is an opaque base64 token that encodes the ID of the last item the client received. The server fetches the next N rows after that ID.

**When to use:** infinite scroll feeds, high-write datasets.

**Advantage:** stable across concurrent inserts — no skipped or duplicated rows.

## Setup

```bash
pip install -r requirements.txt
python seed.py        # populates the local SQLite database
uvicorn main:app --reload
```

Open http://localhost:8000/docs and try both endpoints.

## SQL behind each strategy

```sql
-- Offset: skip (page-1)*limit rows
SELECT * FROM articles ORDER BY id
OFFSET :offset LIMIT :limit;

-- Cursor: fetch rows after the last-seen id
SELECT * FROM articles WHERE id > :last_id ORDER BY id LIMIT :limit;
```
