"""
Tests for 05_mutations: CRUD and mutation payload patterns.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import data_05 as db
import schema as s


@pytest.fixture(autouse=True)
def reset_data():
    db.reset()
    yield
    db.reset()


# ── Pattern A: simple mutations ───────────────────────────────────────────────

def test_create_todo_simple_returns_new_item():
    result = s.schema.execute_sync("""
        mutation {
          createTodoSimple(input: { title: "New task", priority: 3 }) {
            id title done priority
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    todo = result.data["createTodoSimple"]
    assert todo["id"] == "5"
    assert todo["title"] == "New task"
    assert todo["done"] is False
    assert todo["priority"] == 3


def test_toggle_done_simple_flips_status():
    result = s.schema.execute_sync('mutation { toggleDoneSimple(id: "3") { id done } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["toggleDoneSimple"]["done"] is True


def test_toggle_done_simple_missing_id_returns_null():
    result = s.schema.execute_sync('mutation { toggleDoneSimple(id: "999") { id } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["toggleDoneSimple"] is None


# ── Pattern B: mutation payload ───────────────────────────────────────────────

def test_create_todo_success_path():
    result = s.schema.execute_sync("""
        mutation {
          createTodo(input: { title: "Practice pagination", priority: 2 }) {
            ... on CreateTodoSuccess { todo { id title priority } }
            ... on ValidationError  { field message }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert "todo" in result.data["createTodo"]
    assert result.data["createTodo"]["todo"]["title"] == "Practice pagination"


def test_create_todo_empty_title_returns_validation_error():
    result = s.schema.execute_sync("""
        mutation {
          createTodo(input: { title: "" }) {
            ... on ValidationError  { field message }
            ... on CreateTodoSuccess { todo { id } }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert "field" in result.data["createTodo"]
    assert result.data["createTodo"]["field"] == "title"


def test_create_todo_invalid_priority_returns_validation_error():
    result = s.schema.execute_sync("""
        mutation {
          createTodo(input: { title: "Test", priority: 10 }) {
            ... on ValidationError { field message }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert result.data["createTodo"]["field"] == "priority"


def test_update_todo_partial_update_only_changes_provided_fields():
    result = s.schema.execute_sync("""
        mutation {
          updateTodo(id: "3", input: { done: true }) {
            ... on UpdateTodoSuccess { todo { title done priority } }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    todo = result.data["updateTodo"]["todo"]
    assert todo["done"] is True
    assert todo["title"] == "Implement DataLoaders"   # unchanged
    assert todo["priority"] == 2                       # unchanged


def test_update_todo_missing_id_returns_not_found():
    result = s.schema.execute_sync("""
        mutation {
          updateTodo(id: "999", input: { done: true }) {
            ... on TodoNotFound     { id message }
            ... on UpdateTodoSuccess { todo { id } }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert "message" in result.data["updateTodo"]
    assert result.data["updateTodo"]["id"] == "999"


def test_delete_todo_returns_deleted_item():
    result = s.schema.execute_sync("""
        mutation {
          deleteTodo(id: "1") {
            ... on TodoItem     { id title }
            ... on TodoNotFound { message }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert result.data["deleteTodo"]["title"] == "Learn GraphQL schema basics"
    assert len(db.items) == 3


def test_delete_todo_missing_id_returns_not_found():
    result = s.schema.execute_sync("""
        mutation {
          deleteTodo(id: "999") {
            ... on TodoNotFound { id message }
            ... on TodoItem     { id }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert "message" in result.data["deleteTodo"]


def test_two_mutations_run_in_sequence():
    """Multiple mutations in one request run in order, not parallel."""
    result = s.schema.execute_sync("""
        mutation {
          first:  createTodo(input: { title: "First" }) {
            ... on CreateTodoSuccess { todo { id } }
          }
          second: createTodo(input: { title: "Second" }) {
            ... on CreateTodoSuccess { todo { id } }
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert result.data["first"]["todo"]["id"] == "5"
    assert result.data["second"]["todo"]["id"] == "6"


def test_mutation_and_query_reflect_change():
    s.schema.execute_sync("""
        mutation { updateTodo(id: "3", input: { done: true }) {
          ... on UpdateTodoSuccess { todo { id } }
        }}
    """)
    result = s.schema.execute_sync('{ todo(id: "3") { done } }')
    assert result.data is not None
    assert result.data["todo"]["done"] is True
