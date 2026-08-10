"""
Tests for 01_schema_basics.

Strawberry schemas can be tested without a running server using
schema.execute_sync() for sync tests or await schema.execute() for async.

The result has:
  result.data   — the response data dict (None on error)
  result.errors — list of GraphQLError (None on success)
"""

import pytest
import schema as s


@pytest.fixture(autouse=True)
def reset_data():
    s.reset()
    yield
    s.reset()


# ── Queries ───────────────────────────────────────────────────────────────────

def test_books_returns_all_three_seed_books():
    result = s.schema.execute_sync("{ books { id title } }")
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["books"]) == 3


def test_books_only_returns_requested_fields():
    result = s.schema.execute_sync("{ books { title } }")
    assert result.errors is None
    assert result.data is not None
    # No 'year' or 'author' — client asked for title only
    assert all("year" not in book for book in result.data["books"])
    assert result.data["books"][0]["title"] == "Clean Code"


def test_book_by_id_returns_correct_book():
    result = s.schema.execute_sync('{ book(id: "2") { title author } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["book"]["title"] == "The Pragmatic Programmer"
    assert result.data["book"]["author"] == "Hunt & Thomas"


def test_book_by_missing_id_returns_null():
    result = s.schema.execute_sync('{ book(id: "999") { title } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["book"] is None


def test_nullable_description_can_be_null():
    result = s.schema.execute_sync('{ book(id: "1") { description } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["book"]["description"] is None


def test_nullable_description_can_have_value():
    result = s.schema.execute_sync('{ book(id: "3") { description } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["book"]["description"] == "The seminal patterns book"


def test_query_with_named_operation_and_variable():
    result = s.schema.execute_sync(
        "query GetBook($id: ID!) { book(id: $id) { title } }",
        variable_values={"id": "1"},
    )
    assert result.errors is None
    assert result.data is not None
    assert result.data["book"]["title"] == "Clean Code"


def test_alias_fetches_two_books_in_one_request():
    result = s.schema.execute_sync("""
        {
          first:  book(id: "1") { title }
          second: book(id: "2") { title }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert result.data["first"]["title"] == "Clean Code"
    assert result.data["second"]["title"] == "The Pragmatic Programmer"


# ── Mutations ─────────────────────────────────────────────────────────────────

def test_add_book_returns_new_book_with_id():
    result = s.schema.execute_sync("""
        mutation {
          addBook(input: {
            title: "DDIA"
            author: "Kleppmann"
            year: 2017
          }) {
            id title year description
          }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    book = result.data["addBook"]
    assert book["id"] == "4"
    assert book["title"] == "DDIA"
    assert book["description"] is None


def test_add_book_with_description():
    result = s.schema.execute_sync("""
        mutation {
          addBook(input: {
            title: "Refactoring"
            author: "Fowler"
            year: 2018
            description: "Essential reading"
          }) { description }
        }
    """)
    assert result.errors is None
    assert result.data is not None
    assert result.data["addBook"]["description"] == "Essential reading"


def test_add_book_appears_in_list():
    s.schema.execute_sync("""
        mutation {
          addBook(input: { title: "New", author: "Author", year: 2024 }) { id }
        }
    """)
    result = s.schema.execute_sync("{ books { title } }")
    assert result.data is not None
    titles = [b["title"] for b in result.data["books"]]
    assert "New" in titles
    assert len(titles) == 4


def test_delete_book_returns_true_and_removes_it():
    result = s.schema.execute_sync('mutation { deleteBook(id: "1") }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["deleteBook"] is True

    result = s.schema.execute_sync('{ book(id: "1") { title } }')
    assert result.data is not None
    assert result.data["book"] is None


def test_delete_missing_book_returns_false():
    result = s.schema.execute_sync('mutation { deleteBook(id: "999") }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["deleteBook"] is False


def test_mutation_with_variable():
    result = s.schema.execute_sync(
        """
        mutation AddBook($input: AddBookInput!) {
          addBook(input: $input) { title year }
        }
        """,
        variable_values={
            "input": {"title": "The Art of Unix", "author": "ESR", "year": 2003}
        },
    )
    assert result.errors is None
    assert result.data is not None
    assert result.data["addBook"]["title"] == "The Art of Unix"


# ── Schema introspection ──────────────────────────────────────────────────────

def test_schema_has_book_type():
    result = s.schema.execute_sync("""
        { __type(name: "Book") { name fields { name } } }
    """)
    assert result.errors is None
    assert result.data is not None
    field_names = {f["name"] for f in result.data["__type"]["fields"]}
    assert {"id", "title", "author", "year", "description"}.issubset(field_names)
