"""
04 · Types — Concepts
======================

CONTENTS:
  1. Enums
  2. Custom scalars — dates, UUIDs, JSON
  3. Interfaces — shared shape across types
  4. Unions — "one of these types"
  5. Interface vs Union — when to use each
  6. Inline fragments — querying union / interface fields
  7. Exercises

--- ENUMS ---

    @strawberry.enum
    class Genre:
        FICTION     = "fiction"
        NON_FICTION = "non_fiction"

SDL output:
    enum Genre {
      FICTION
      NON_FICTION
    }

Use enums for fields with a fixed set of valid values.
Benefits:
  - Schema-validated: the client can only send valid enum values
  - Documented: introspection shows all options
  - Refactoring-safe: rename in one place

--- CUSTOM SCALARS ---

GraphQL has 5 built-in scalars. For everything else (dates, UUIDs, JSON,
money, email), define a custom scalar:

    Date = strawberry.scalar(
        date,                               # Python type
        name="Date",                        # name in SDL
        description="ISO 8601 date",
        serialize=lambda v: v.isoformat(),  # Python → JSON
        parse_value=lambda v: date.fromisoformat(v),  # JSON → Python
    )

    @strawberry.type
    class Article:
        published_at: Optional[Date] = None

SDL:
    scalar Date

    type Article {
      publishedAt: Date
    }

Common custom scalars:
  Date     — datetime.date  →  "2024-01-15"
  DateTime — datetime       →  "2024-01-15T10:30:00Z"
  UUID     — uuid.UUID      →  "550e8400-e29b-41d4-a716-446655440000"
  JSON     — dict           →  raw JSON object

--- INTERFACES ---

    @strawberry.interface
    class Publishable:
        title: str
        status: PublishStatus

    @strawberry.type
    class Article(Publishable):
        title: str               # must include interface fields
        status: PublishStatus
        body: str                # plus type-specific fields

SDL:
    interface Publishable {
      title: String!
      status: PublishStatus!
    }

    type Article implements Publishable {
      title: String!
      status: PublishStatus!
      body: String!
    }

Querying interfaces: the shared fields are directly accessible,
type-specific fields need an inline fragment.

    query {
      content {
        title          # from interface — works on all types
        status
        ... on Article { body }   # Article-specific
        ... on Video   { url }    # Video-specific
      }
    }

--- UNIONS ---

    SearchResult = strawberry.union("SearchResult", types=(Article, Video))

SDL:
    union SearchResult = Article | Video

Unions have NO shared fields. You must always use inline fragments:

    query {
      search(term: "GraphQL") {
        ... on Article { id title body }
        ... on Video   { id title url }
      }
    }

Use __typename to know which type you got:
    query {
      search(term: "GraphQL") {
        __typename
        ... on Article { body }
        ... on Video   { url }
      }
    }

--- INTERFACE vs UNION ---

Interface: types share a common shape (shared fields accessible without fragments)
Union:      types have nothing in common (always need inline fragments)

Use interface when:
  - You want to query shared fields without inline fragments
  - The types represent variations of the same concept (Article / Post / Page)
  - You want type-checking guarantees (all implementors must have these fields)

Use union when:
  - The types are unrelated (User | Post for a "mentions" feed)
  - There are no meaningful shared fields
  - You need a "result OR error" type (see section 05)

--- EXERCISES ---

1. Query articles filtered by genre:
       { articlesByGenre(genre: NON_FICTION) { title } }

2. Search for content matching "GraphQL":
       { search(term: "GraphQL") {
           __typename
           ... on Article { title body }
           ... on Video { title url }
         }
       }

3. Query published content and use inline fragments to get type-specific fields.

4. Try passing an invalid enum value:
       { articlesByGenre(genre: ROMANCE) { title } }
   The schema rejects it with a validation error.

5. Observe the custom scalar: article(id: "a1") { publishedAt }
   The Date scalar serializes Python date → "2024-01-15" string.

6. Add a Podcast type that also implements Publishable.
   Update the union and query to include podcasts.
"""

INTERFACE_VS_UNION = {
    "Interface": "Types share fields — query shared fields without fragments",
    "Union":     "Types unrelated — always need inline fragments",
}

SCALAR_CREATION = """
Date = strawberry.scalar(
    date,
    name="Date",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: date.fromisoformat(v),
)
"""

INLINE_FRAGMENT_SYNTAX = """
# Query a union or interface type-specific fields:
query {
  search(term: "GraphQL") {
    __typename          # "Article" or "Video"
    ... on Article {    # only runs for Article instances
      body
      genre
    }
    ... on Video {      # only runs for Video instances
      url
      durationSeconds
    }
  }
}
"""
