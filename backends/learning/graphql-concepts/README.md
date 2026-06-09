# GraphQL Concepts

Hands-on GraphQL practice using **Strawberry** (Python) and **FastAPI**.
Each section is self-contained with a runnable schema, concept notes, and tests.

## Stack

| | |
|---|---|
| Schema library | [Strawberry](https://strawberry.rocks) — code-first, type-annotated |
| HTTP server    | FastAPI + GraphQL playground |
| Testing        | `schema.execute_sync()` / `await schema.execute()` — no HTTP needed |

## Setup

```bash
pip install -r requirements.txt
```

## Sections

| # | Folder | Key concepts |
|---|--------|-------------|
| 1 | `01_schema_basics/` | `@strawberry.type`, scalars, queries, mutations, input types |
| 2 | `02_relationships/` | Nested resolver methods, `strawberry.Private`, N+1 problem |
| 3 | `03_dataloaders/`   | `strawberry.dataloader`, batching, per-request context |
| 4 | `04_types/`         | Enums, custom scalars (Date), interfaces, unions, inline fragments |
| 5 | `05_mutations/`     | CRUD, partial updates, mutation payload / typed error unions |
| 6 | `06_pagination/`    | Offset pagination, Relay cursor pagination, PageInfo |

Each section has:
- `schema.py` — the runnable schema with inline comments
- `notes.py` — concept explanations, query examples, exercises
- `test_schema.py` — pytest tests

## Run the tests

```bash
# All sections at once
pytest

# One section
pytest 02_relationships/
```

## Run the interactive playground

```bash
uvicorn app:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) to see all sections,
or navigate directly to a section's playground:

| Section | Playground URL |
|---------|---------------|
| 01 Schema Basics    | http://localhost:8000/01/graphql |
| 02 Relationships    | http://localhost:8000/02/graphql |
| 03 DataLoaders      | http://localhost:8000/03/graphql |
| 04 Types            | http://localhost:8000/04/graphql |
| 05 Mutations        | http://localhost:8000/05/graphql |
| 06 Pagination       | http://localhost:8000/06/graphql |

## Key GraphQL vs REST differences

```
REST: server decides the response shape
  GET /books/1 → { id, title, author, year, description, ... }

GraphQL: client decides which fields to include
  { book(id: "1") { title year } } → { book: { title, year } }
```

No over-fetching. No under-fetching. Multiple resources in one request.

## Progression

Work through the sections in order — each builds on the previous:
1. Start with the schema basics to understand types and SDL
2. Add relationships and see the N+1 problem appear
3. Fix N+1 with DataLoaders
4. Explore the full type system (enums, unions, interfaces)
5. Practice real-world mutation patterns with typed errors
6. Add pagination to list queries
