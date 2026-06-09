"""
01 · Schema Basics
==================

The absolute minimum: one type, a query, and a mutation.
Run the tests to see queries in action, or spin up app.py and use the playground.
"""

import strawberry
from typing import Optional

# ── 1. Object type ────────────────────────────────────────────────────────────
#
# @strawberry.type maps a Python class to a GraphQL object type.
# Type annotations become field types:
#
#   str           → String!   (non-nullable, required in responses)
#   int           → Int!
#   Optional[str] → String    (nullable, may be null in responses)
#   list[Book]    → [Book!]!  (non-null list of non-null Books)
#
# strawberry.ID is a special scalar — identical to String in the wire protocol
# but signals "this is an identifier" to clients and tooling.

@strawberry.type
class Book:
    id: strawberry.ID
    title: str
    author: str
    year: int
    description: Optional[str] = None   # nullable — absent in some books


# ── 2. In-memory store ────────────────────────────────────────────────────────

_SEED: list[dict] = [
    {"id": "1", "title": "Clean Code",              "author": "Robert C. Martin", "year": 2008, "description": None},
    {"id": "2", "title": "The Pragmatic Programmer", "author": "Hunt & Thomas",   "year": 2019, "description": "Updated for a new generation"},
    {"id": "3", "title": "Design Patterns",          "author": "Gang of Four",    "year": 1994, "description": "The seminal patterns book"},
]

_books: list[dict] = [row.copy() for row in _SEED]
_next_id: int = 4


def reset() -> None:
    """Restore seed data — called by the pytest fixture between tests."""
    global _books, _next_id
    _books = [row.copy() for row in _SEED]
    _next_id = 4


def _row_to_book(row: dict) -> Book:
    return Book(**row)


# ── 3. Query ──────────────────────────────────────────────────────────────────
#
# The Query class defines all read operations.
# Each @strawberry.field method becomes a queryable field in the schema.

@strawberry.type
class Query:

    @strawberry.field
    def books(self) -> list[Book]:
        return [_row_to_book(b) for b in _books]

    @strawberry.field
    def book(self, id: strawberry.ID) -> Optional[Book]:
        row = next((b for b in _books if b["id"] == id), None)
        return _row_to_book(row) if row else None


# ── 4. Input type ─────────────────────────────────────────────────────────────
#
# @strawberry.input is used ONLY for mutation arguments.
# Input types cannot have resolver methods — they are plain data containers.

@strawberry.input
class AddBookInput:
    title: str
    author: str
    year: int
    description: Optional[str] = None


# ── 5. Mutation ───────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:

    @strawberry.mutation
    def add_book(self, input: AddBookInput) -> Book:
        global _next_id
        row = {
            "id": str(_next_id),
            "title": input.title,
            "author": input.author,
            "year": input.year,
            "description": input.description,
        }
        _books.append(row)
        _next_id += 1
        return _row_to_book(row)

    @strawberry.mutation
    def delete_book(self, id: strawberry.ID) -> bool:
        for i, b in enumerate(_books):
            if b["id"] == id:
                _books.pop(i)
                return True
        return False


# ── 6. Schema ─────────────────────────────────────────────────────────────────
#
# strawberry.Schema is the entry point.
# query= is required; mutation= and subscription= are optional.

schema = strawberry.Schema(query=Query, mutation=Mutation)
