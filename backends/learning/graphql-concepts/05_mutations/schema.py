"""
05 · Mutations — CRUD & Error Handling
=======================================

Two mutation patterns shown side-by-side:
  A. Simple boolean/nullable return — straightforward but no error info
  B. Mutation payload with union return — structured, typed error info
"""

import strawberry
from typing import Optional, Annotated, Union

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import data_05 as db


# ── Type ──────────────────────────────────────────────────────────────────────

@strawberry.type
class TodoItem:
    id: strawberry.ID
    title: str
    done: bool
    priority: int


def _row_to_todo(row: dict) -> TodoItem:
    return TodoItem(**row)


# ── Pattern A: Simple mutations ───────────────────────────────────────────────
#
# Return the created/updated object or a simple bool.
# Simple to write but gives clients no structured error info.
# If something goes wrong you only have HTTP 200 with `data: null`.

@strawberry.input
class CreateTodoInput:
    title: str
    priority: Optional[int] = 1


@strawberry.input
class UpdateTodoInput:
    title: Optional[str] = None
    done: Optional[bool] = None
    priority: Optional[int] = None


# ── Pattern B: Mutation payload with typed errors ─────────────────────────────
#
# The "mutation payload" pattern: return a union of success / error types.
# Clients can use inline fragments to handle each case explicitly.
# This is the recommended pattern for any mutation that can fail.

@strawberry.type
class TodoNotFound:
    id: strawberry.ID
    message: str = "Todo item not found"


@strawberry.type
class ValidationError:
    field: str
    message: str


@strawberry.type
class CreateTodoSuccess:
    todo: TodoItem


@strawberry.type
class UpdateTodoSuccess:
    todo: TodoItem


# Union types for mutation results
# Modern Strawberry: Annotated[Union[TypeA, TypeB], strawberry.union("Name")]
CreateTodoResult = Annotated[
    Union[CreateTodoSuccess, ValidationError],
    strawberry.union("CreateTodoResult"),
]

UpdateTodoResult = Annotated[
    Union[UpdateTodoSuccess, TodoNotFound, ValidationError],
    strawberry.union("UpdateTodoResult"),
]

DeleteTodoResult = Annotated[
    Union[TodoItem, TodoNotFound],
    strawberry.union("DeleteTodoResult"),
]


# ── Mutations ─────────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:

    # ── Pattern A: simple returns ─────────────────────────────────────────────

    @strawberry.mutation
    def create_todo_simple(self, input: CreateTodoInput) -> TodoItem:
        """Returns the created item. Can't express errors structurally."""
        global db
        row = {
            "id": str(db._next_id),
            "title": input.title,
            "done": False,
            "priority": input.priority or 1,
        }
        db.items.append(row)
        db._next_id += 1
        return _row_to_todo(row)

    @strawberry.mutation
    def toggle_done_simple(self, id: strawberry.ID) -> Optional[TodoItem]:
        """Returns None if not found — client must check for null."""
        for item in db.items:
            if item["id"] == id:
                item["done"] = not item["done"]
                return _row_to_todo(item)
        return None

    # ── Pattern B: mutation payload with typed errors ─────────────────────────

    @strawberry.mutation
    def create_todo(
        self, input: CreateTodoInput
    ) -> CreateTodoResult:
        """
        Returns CreateTodoSuccess or ValidationError.
        Clients use inline fragments:
          ... on CreateTodoSuccess { todo { id title } }
          ... on ValidationError  { field message }
        """
        if not input.title.strip():
            return ValidationError(field="title", message="Title cannot be empty")
        if input.priority and not (1 <= input.priority <= 5):
            return ValidationError(field="priority", message="Priority must be 1–5")

        row = {
            "id": str(db._next_id),
            "title": input.title.strip(),
            "done": False,
            "priority": input.priority or 1,
        }
        db.items.append(row)
        db._next_id += 1
        return CreateTodoSuccess(todo=_row_to_todo(row))

    @strawberry.mutation
    def update_todo(
        self, id: strawberry.ID, input: UpdateTodoInput
    ) -> UpdateTodoResult:
        """
        Returns UpdateTodoSuccess, TodoNotFound, or ValidationError.
        Partial update — only provided fields are changed.
        """
        row = next((item for item in db.items if item["id"] == id), None)
        if row is None:
            return TodoNotFound(id=id)

        if input.title is not None:
            if not input.title.strip():
                return ValidationError(field="title", message="Title cannot be empty")
            row["title"] = input.title.strip()

        if input.done is not None:
            row["done"] = input.done

        if input.priority is not None:
            if not (1 <= input.priority <= 5):
                return ValidationError(field="priority", message="Priority must be 1–5")
            row["priority"] = input.priority

        return UpdateTodoSuccess(todo=_row_to_todo(row))

    @strawberry.mutation
    def delete_todo(
        self, id: strawberry.ID
    ) -> DeleteTodoResult:
        """Returns the deleted item on success, TodoNotFound if missing."""
        for i, item in enumerate(db.items):
            if item["id"] == id:
                row = db.items.pop(i)
                return _row_to_todo(row)
        return TodoNotFound(id=id)


# ── Query ─────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:

    @strawberry.field
    def todos(self) -> list[TodoItem]:
        return [_row_to_todo(item) for item in db.items]

    @strawberry.field
    def todo(self, id: strawberry.ID) -> Optional[TodoItem]:
        row = next((item for item in db.items if item["id"] == id), None)
        return _row_to_todo(row) if row else None


schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    types=[CreateTodoSuccess, UpdateTodoSuccess, TodoNotFound, ValidationError, TodoItem],
)
