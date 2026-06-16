# 02 · Relationships & N+1 — Concepts

CONTENTS:
  1. Resolver methods on types
  2. strawberry.Private — internal fields
  3. The N+1 problem — why it happens and how to measure it
  4. Exercises

## RESOLVER METHODS

A method decorated with @strawberry.field on a type class becomes a
"field resolver" — called when the client requests that field.

    @strawberry.type
    class Author:
        id: strawberry.ID
        name: str

        @strawberry.field
        def posts(self) -> list[Post]:
            # This runs once per Author in the response
            return db.get_posts_by_author(str(self.id))

The method receives `self` (the current Author instance) and can use
it to load related data. No arguments needed from the client unless
you want to add filtering/pagination.

## strawberry.Private

Fields on @strawberry.type are exposed in the schema by default.
Sometimes you need to carry internal state (like a foreign key ID)
through the type to use in a resolver, but you don't want it
visible in the GraphQL schema.

    @strawberry.type
    class Post:
        id: strawberry.ID
        title: str
        author_id: strawberry.Private[str]  # NOT in schema

        @strawberry.field
        def author(self) -> Author:
            return db.get_author(self.author_id)

strawberry.Private[T] removes the field from the generated schema
while keeping it available in Python as a regular attribute.

## THE N+1 PROBLEM

Scenario: a client queries all posts with their author names.

    query {
      posts {
        title
        author { name }
      }
    }

What happens with the naive resolver:
  1. Query: SELECT * FROM posts                → 1 query, returns 6 posts
  2. For each post, resolve .author:
       get_author("a1")                        → 1 query
       get_author("a1")  (second post)         → 1 query (duplicate!)
       get_author("a2")                        → 1 query
       get_author("a2")  (second post)         → 1 query (duplicate!)
       get_author("a3")                        → 1 query
       get_author("a3")  (second post)         → 1 query (duplicate!)
                                              ────────────────────────
  Total: 1 + 6 = 7 queries to load 6 posts   ← the N+1 problem

With 100 posts and 30 distinct authors, it's 1 + 100 = 101 queries.

Why "N+1"? You make 1 query for the list, then N queries for the
related object — one per item in the list.

The fix is DataLoader (section 03): batch all author IDs from the
entire post list into a SINGLE get_authors([id1, id2, id3]) call.
Total drops from 7 to 2 (1 for posts, 1 for all authors).

## MEASURING N+1

data.py uses a QueryCounter to count and print every "DB" call.
After running a query, check data.QueryCounter.calls.

In tests:
    db.reset()
    schema.execute_sync("{ posts { author { name } } }")
    assert db.QueryCounter.calls == 1 + len(db.posts)  # 7: N+1!

Section 03 (DataLoaders) reduces this to 2.

## EXERCISES

1. Query all posts without requesting the author field.
   Check QueryCounter.calls — it should be 1 (just the posts list).
   Then add { author { name } } — calls jumps to 7.

2. Query a single post with its author. How many calls?
   (1 for post lookup, 1 for author = 2 total)

3. Query all authors with their posts:
       { authors { name posts { title } } }
   How many calls? (1 for authors list + 3 posts queries = 4)

4. Try to add a query that loads authors with their posts AND each
   post's author (circular). What does GraphQL do?
   (It follows the resolvers to their natural conclusion — infinite
   loops are possible if you don't add depth limiting.)

## Quick reference (preserved from the original notes)

```python
N_PLUS_ONE_EXAMPLE = {
    "query":          "{ posts { author { name } } }",
    "n_posts":        6,
    "expected_naive": "1 (posts) + 6 (one get_author per post) = 7 queries",
    "expected_dl":    "1 (posts) + 1 (batch get_authors) = 2 queries",
    "improvement":    "7 → 2 queries regardless of how many posts/authors",
}

PRIVATE_FIELD_PATTERN = {
    "purpose":   "Carry a FK/internal value through the type for resolver use",
    "syntax":    "author_id: strawberry.Private[str]",
    "effect":    "Not included in the generated SDL or introspection response",
    "use_cases": ["Foreign key IDs for DataLoader", "Request-scoped metadata", "Internal flags"],
}
```

