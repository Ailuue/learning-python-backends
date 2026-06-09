"""
04 · Types — Enums, Unions, Interfaces, Custom Scalars
=======================================================

The GraphQL type system beyond basic objects and scalars.
"""

import enum as _enum
import strawberry
from typing import Annotated, Optional, Union
from datetime import date


# ── 1. Enums ─────────────────────────────────────────────────────────────────
#
# @strawberry.enum wraps a Python stdlib enum.Enum class.
# The enum members become GraphQL enum values.

@strawberry.enum
class Genre(_enum.Enum):
    FICTION     = "fiction"
    NON_FICTION = "non_fiction"
    SCIENCE     = "science"
    HISTORY     = "history"


@strawberry.enum
class PublishStatus(_enum.Enum):
    DRAFT     = "draft"
    PUBLISHED = "published"
    ARCHIVED  = "archived"


# ── 2. Custom scalar ─────────────────────────────────────────────────────────
#
# For types not built into GraphQL (dates, UUIDs, JSON, etc.),
# define a custom scalar with serialize/parse functions.
#
# Note: Strawberry 0.220+ prefers StrawberryConfig.scalar_map for type safety.
# The strawberry.scalar(type, ...) form still works and is clearer for learning.

Date = strawberry.scalar(
    date,
    name="Date",
    description="ISO 8601 date string (YYYY-MM-DD)",
    serialize=lambda v: v.isoformat(),
    parse_value=lambda v: date.fromisoformat(v),
)


# ── 3. Interface ──────────────────────────────────────────────────────────────
#
# An interface declares fields that all implementing types must have.

@strawberry.interface
class Node:
    id: strawberry.ID


@strawberry.interface
class Publishable:
    title: str
    status: PublishStatus
    published_at: Optional[Date] = None


# ── 4. Types implementing interfaces ─────────────────────────────────────────
#
# A type "implements" an interface by inheriting from it.

@strawberry.type
class Article(Node, Publishable):
    id: strawberry.ID
    title: str
    status: PublishStatus
    body: str
    genre: Genre
    published_at: Optional[Date] = None


@strawberry.type
class Video(Node, Publishable):
    id: strawberry.ID
    title: str
    status: PublishStatus
    url: str
    duration_seconds: int
    published_at: Optional[Date] = None


# ── 5. Union ──────────────────────────────────────────────────────────────────
#
# A union says "this field returns one of these types."
# Defined with Annotated[Union[TypeA, TypeB], strawberry.union("Name")].
#
# Clients use inline fragments to access type-specific fields:
#   { search { ... on Article { body } ... on Video { url } } }

SearchResult = Annotated[
    Union[Article, Video],
    strawberry.union("SearchResult", description="An article or a video"),
]


# ── 6. In-memory data ─────────────────────────────────────────────────────────

_ARTICLES: list[Article] = [
    Article(id="a1", title="GraphQL Basics",   status=PublishStatus.PUBLISHED,
            body="GraphQL is...", genre=Genre.NON_FICTION,
            published_at=date(2024, 1, 15)),
    Article(id="a2", title="Draft Post",        status=PublishStatus.DRAFT,
            body="WIP...", genre=Genre.SCIENCE),
]

_VIDEOS: list[Video] = [
    Video(id="v1", title="Intro to Strawberry", status=PublishStatus.PUBLISHED,
          url="https://example.com/v1", duration_seconds=600,
          published_at=date(2024, 3, 20)),
]


# ── 7. Query ─────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field
    def articles(self) -> list[Article]:
        return _ARTICLES

    @strawberry.field
    def article(self, id: strawberry.ID) -> Optional[Article]:
        return next((a for a in _ARTICLES if a.id == id), None)

    @strawberry.field
    def search(self, term: str) -> list[SearchResult]:
        results: list = []
        for a in _ARTICLES:
            if term.lower() in a.title.lower():
                results.append(a)
        for v in _VIDEOS:
            if term.lower() in v.title.lower():
                results.append(v)
        return results

    @strawberry.field
    def published_content(self) -> list[SearchResult]:
        results: list = []
        results.extend(a for a in _ARTICLES if a.status == PublishStatus.PUBLISHED)
        results.extend(v for v in _VIDEOS if v.status == PublishStatus.PUBLISHED)
        return results

    @strawberry.field
    def articles_by_genre(self, genre: Genre) -> list[Article]:
        return [a for a in _ARTICLES if a.genre == genre]


schema = strawberry.Schema(query=Query, types=[Article, Video])
