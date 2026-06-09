"""
06 · Pagination — Concepts
===========================

CONTENTS:
  1. Why paginate — why not return everything
  2. Offset pagination — pages, total count, problems
  3. Cursor pagination — the Relay Connection spec
  4. Offset vs cursor — when to use each
  5. Relay Connection spec in detail
  6. Exercises

--- WHY PAGINATE ---

A list query with no pagination:
    { posts { id title body } }     # 1,000,000 posts? The server dies.

Every list that can grow unboundedly needs pagination.
Design it from the start — retrofitting pagination is painful.

--- OFFSET PAGINATION ---

    query {
      postsPage(offset: 20, limit: 10) {
        items { id title }
        total
        hasNextPage
        hasPrevPage
      }
    }

Pros:
  - Simple to implement (SQL: LIMIT 10 OFFSET 20)
  - Easy to jump to any page: page N = offset (N-1)*limit
  - Familiar to clients (page 1, 2, 3...)

Cons:
  - Inconsistent under concurrent mutations:
      - You load page 1 (items 1-10)
      - Another user deletes item 3
      - You load page 2 (items 11-20, but item 11 was what should be item 10)
      - Item 10 is skipped entirely — you never see it
  - Expensive for large offsets in SQL (OFFSET 1000000 scans 1M rows)

--- CURSOR PAGINATION ---

    query {
      postsConnection(first: 10) {
        edges {
          cursor
          node { id title }
        }
        pageInfo {
          hasNextPage
          endCursor    ← use this as `after` for the next page
        }
        totalCount
      }
    }

Next page:
    query {
      postsConnection(first: 10, after: "cG9zdDoxMA==") {
        edges { node { id title } }
        pageInfo { hasNextPage endCursor }
      }
    }

Pros:
  - Stable: cursor points to a specific item, not a position
  - No skipped or duplicated items under concurrent mutations
  - Efficient: cursor-based WHERE id > last_id uses an index

Cons:
  - Can't jump to "page 5" — must page through sequentially
  - More complex to implement
  - Cursors are opaque (clients can't interpret them)

--- WHEN TO USE EACH ---

Use offset when:
  - Users navigate by page number ("Go to page 5")
  - The dataset is small and rarely mutated
  - Simple admin interfaces

Use cursor when:
  - Infinite scroll / "load more" button (most social feeds)
  - Real-time data (tweets, notifications)
  - Large datasets
  - Consistency matters

--- RELAY CONNECTION SPEC ---

The Relay specification (from Facebook/Meta) defines a standard cursor
pagination interface. Clients built for Relay understand this shape.

SDL for a Relay-style connection:
    type PostEdge {
      node: Post!
      cursor: String!
    }

    type PageInfo {
      hasNextPage: Boolean!
      hasPreviousPage: Boolean!
      startCursor: String
      endCursor: String
    }

    type PostConnection {
      edges: [PostEdge!]!
      pageInfo: PageInfo!
      totalCount: Int!
    }

Arguments on the connection field:
  first: Int    — number of items to return (forward pagination)
  after: String — cursor to start after (forward pagination)
  last: Int     — number of items before cursor (backward pagination)
  before: String — cursor to end before (backward pagination)

Cursors are opaque base64 strings. Our implementation encodes "post:<id>":
  encode("post:42") = "cG9zdDo0Mg=="
  decode("cG9zdDo0Mg==") = "42"

The Relay spec says cursors should be opaque — clients MUST NOT
parse or construct them, only pass them back to the server.

--- STRAWBERRY.RELAY ---

Strawberry provides built-in Relay support in `strawberry.relay`:

    import strawberry
    from strawberry import relay

    @strawberry.type
    class PostNode(relay.Node):
        id: relay.NodeID[int]  # resolves to GlobalID automatically
        title: str

        @classmethod
        def resolve_nodes(cls, *, info, node_ids, required=False):
            return [get_post(id) for id in node_ids]

    @strawberry.type
    class Query:
        posts: relay.ListConnection[PostNode] = relay.connection(
            resolver=lambda: all_posts()
        )

This generates the full Connection/Edge/PageInfo types automatically.
The manual implementation in schema.py shows what it's doing internally.

--- EXERCISES ---

1. Fetch the first page (offset=0, limit=5):
       { postsPage(offset: 0, limit: 5) { items { id title } total hasNextPage } }

2. Fetch the second page and check hasPrevPage:
       { postsPage(offset: 5, limit: 5) { items { id title } hasPrevPage hasNextPage } }

3. Cursor-paginate through all 100 posts with first: 25:
   - Fetch first page, note the endCursor
   - Fetch second page using after: "<endCursor>"
   - Repeat. The fourth page should have hasNextPage: false.

4. Observe cursor stability:
   - Fetch a cursor from page 1
   - Imagine deleting the first item (no API for this here, but think through)
   - With offset: the second fetch of "offset: 5" now returns a shifted result
   - With cursor: the next page starts after the cursor item — no shift

5. Decode a cursor:
   import base64
   cursor = "cG9zdDoxMA=="
   base64.b64decode(cursor).decode()  # → "post:10"
"""

PAGINATION_COMPARISON = {
    "Offset": {
        "query_args":  "offset: Int, limit: Int",
        "pros":        "Simple, supports page numbers",
        "cons":        "Drift under mutations, O(offset) scan",
        "use_for":     "Admin tables, small static datasets",
    },
    "Cursor": {
        "query_args":  "first: Int, after: String",
        "pros":        "Stable, efficient, real-time safe",
        "cons":        "No random-access page jump",
        "use_for":     "Feeds, infinite scroll, large datasets",
    },
}

RELAY_SHAPE = {
    "connection": "{ edges { node cursor } pageInfo { hasNextPage endCursor } totalCount }",
    "page_args":  "first: Int, after: String  (or last + before for backward)",
    "cursor":     "Opaque base64 string — do not parse client-side",
}
