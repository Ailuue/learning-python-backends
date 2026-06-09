"""
03 · DataLoaders — Concepts
============================

CONTENTS:
  1. What a DataLoader does
  2. The batching mechanism — how keys are collected
  3. Per-request lifecycle
  4. The ordering contract
  5. Caching within a request
  6. Using context to pass loaders to resolvers
  7. Exercises

--- WHAT A DATALOADER DOES ---

Problem: N post resolvers each call get_author(id) independently
→ N separate queries to the database.

DataLoader solution:
  1. Post resolver 1 calls loader.load("a1") — does NOT query the DB yet
  2. Post resolver 2 calls loader.load("a1") — same key, queued
  3. Post resolver 3 calls loader.load("a2") — different key, queued
  ... (all 6 post resolvers queue their author_id)
  4. GraphQL executor finishes queuing this batch of resolvers
  5. DataLoader fires batch_load_authors(["a1", "a1", "a2", "a2", "a3", "a3"])
     — or deduplicated: ["a1", "a2", "a3"]
  6. Returns one Author dict per post resolver

Result: N individual DB calls → 1 batch call. Always.

--- THE BATCHING MECHANISM ---

DataLoaders use the event loop's "tick" to collect keys:

    loader.load("a1")   # queued
    loader.load("a2")   # queued
    loader.load("a3")   # queued
    # await — yields to the event loop
    # DataLoader fires batch_load_authors(["a1", "a2", "a3"])
    # returns results to each awaiter

In Strawberry, the executor awaits all field resolvers in the same
depth level simultaneously. This is why "all post.author resolvers
run in the same tick" — Strawberry schedules them all before awaiting.

--- PER-REQUEST LIFECYCLE ---

CRITICAL: create a new DataLoader for each request.

    # WRONG — singleton caches stale data across requests
    author_loader = make_author_loader()

    # CORRECT — fresh loader per request
    def get_context():
        return {"author_loader": make_author_loader()}

Why? The DataLoader caches keys within its lifetime. If you share one
DataLoader across requests, a cached author from request 1 might be
served to request 2, even after the author was updated.

--- THE ORDERING CONTRACT ---

Your batch function MUST return results in the SAME ORDER as the input keys:

    async def batch_load(keys: list[str]) -> list[T | None]:
        rows = await db.query("SELECT * FROM authors WHERE id = ANY($1)", keys)
        index = {row.id: row for row in rows}
        return [index.get(key) for key in keys]  # ← same order as keys

NOT:
    return rows  # ← rows might be in any order from the DB

If the order doesn't match, callers receive wrong data silently.

--- CACHING WITHIN A REQUEST ---

The DataLoader caches results within one request. If two fields in the
same query ask for the same author, the second load() returns the cached
result without a second batch call.

    query {
      posts {          # 6 posts, authors a1/a2/a3 loaded in one batch
        author { name }
      }
    }

    # author "a1" requested by posts p1 and p2 → loaded once, cached for p2

To disable caching (e.g., for write-heavy operations):
    DataLoader(load_fn=batch_load, cache=False)

--- USING CONTEXT TO PASS LOADERS ---

Resolvers access the DataLoader via info.context:

    @strawberry.field
    async def author(self, info: Info) -> Author:
        row = await info.context["author_loader"].load(self.author_id)
        return Author(**row)

For tests, pass context directly to schema.execute():
    context = {"author_loader": make_author_loader()}
    await schema.execute(query, context_value=context)

For FastAPI, use a context_getter:
    async def get_context() -> dict:
        return {"author_loader": make_author_loader()}

    router = GraphQLRouter(schema, context_getter=get_context)

--- EXERCISES ---

1. Verify the improvement:
   Add prints to batch_load_authors() and run the posts+author query.
   Confirm it prints once (not 6 times).

2. Test with data.BatchCounter:
   After running { posts { author { name } } } with the DL schema:
     assert db.BatchCounter.calls == 1   (vs 6 in section 02)

3. Add a posts DataLoader:
   Create batch_load_posts(author_ids) and use it in an Author.posts resolver.
   Verify that { authors { posts { title } } } makes 1 batch call
   (not 3 individual calls like section 02).

4. Observe the caching:
   Add a counter to batch_load_authors.
   Run: { post(id: "p1") { author { name } } }  twice in the same context.
   The second query should hit the cache — batch_load fires once total.
"""

DATALOADER_LIFECYCLE = [
    "1. Resolver calls loader.load(key) — returns a coroutine, does not query",
    "2. All resolvers in the same depth level do the same",
    "3. Event loop tick completes — DataLoader fires batch_load_fn([all keys])",
    "4. Results distributed back to each awaiting resolver",
]

BATCH_FUNCTION_CONTRACT = {
    "input":  "list[key] — all keys requested in this tick",
    "output": "list[value | None] — same length, same ORDER as input",
    "why":    "DataLoader matches result[i] to the caller of load(keys[i])",
}

COMMON_MISTAKES = {
    "singleton_loader": "Sharing one loader across requests → stale cache",
    "wrong_order":      "Returning batch results in DB order not input order → wrong data",
    "sync_load":        "Calling loader.load() without await → resolver returns a coroutine",
    "missing_context":  "Not passing context to schema.execute() → info.context is None",
}
