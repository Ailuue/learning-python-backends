"""
Tests for 06_pagination: offset and cursor pagination.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import data_06 as db
import schema as s


@pytest.fixture(autouse=True)
def reset_data():
    db.reset()
    yield
    db.reset()


# ── Offset pagination ─────────────────────────────────────────────────────────

def test_offset_first_page_returns_correct_items():
    result = s.schema.execute_sync("""
        { postsPage(offset: 0, limit: 5) { items { id title } total hasNextPage hasPrevPage } }
    """)
    assert result.errors is None
    page = result.data["postsPage"]
    assert len(page["items"]) == 5
    assert page["items"][0]["id"] == "1"
    assert page["total"] == 100
    assert page["hasNextPage"] is True
    assert page["hasPrevPage"] is False


def test_offset_second_page_has_prev_page():
    result = s.schema.execute_sync(
        "{ postsPage(offset: 5, limit: 5) { items { id } hasPrevPage } }"
    )
    assert result.errors is None
    page = result.data["postsPage"]
    assert page["items"][0]["id"] == "6"
    assert page["hasPrevPage"] is True


def test_offset_last_page_has_no_next():
    result = s.schema.execute_sync(
        "{ postsPage(offset: 95, limit: 10) { items { id } hasNextPage } }"
    )
    assert result.errors is None
    page = result.data["postsPage"]
    assert len(page["items"]) == 5   # only 5 left
    assert page["hasNextPage"] is False


def test_offset_default_limit_is_ten():
    result = s.schema.execute_sync("{ postsPage { items { id } } }")
    assert result.errors is None
    assert len(result.data["postsPage"]["items"]) == 10


# ── Cursor pagination ─────────────────────────────────────────────────────────

def test_cursor_first_page_returns_correct_items():
    result = s.schema.execute_sync("""
        {
          postsConnection(first: 5) {
            edges { node { id title } cursor }
            pageInfo { hasNextPage hasPrevPage startCursor endCursor }
            totalCount
          }
        }
    """)
    assert result.errors is None
    conn = result.data["postsConnection"]
    assert len(conn["edges"]) == 5
    assert conn["edges"][0]["node"]["id"] == "1"
    assert conn["totalCount"] == 100
    assert conn["pageInfo"]["hasNextPage"] is True
    assert conn["pageInfo"]["hasPrevPage"] is False
    assert conn["pageInfo"]["endCursor"] is not None


def test_cursor_second_page_starts_after_end_cursor():
    # Get first page
    result1 = s.schema.execute_sync(
        "{ postsConnection(first: 5) { pageInfo { endCursor } } }"
    )
    end_cursor = result1.data["postsConnection"]["pageInfo"]["endCursor"]

    # Get second page using the cursor
    result2 = s.schema.execute_sync(
        f'{{ postsConnection(first: 5, after: "{end_cursor}") {{ edges {{ node {{ id }} }} }} }}'
    )
    assert result2.errors is None
    edges = result2.data["postsConnection"]["edges"]
    assert len(edges) == 5
    assert edges[0]["node"]["id"] == "6"   # starts right after post 5


def test_cursor_last_page_has_no_next():
    """Page through all 100 posts in batches of 10; the final page has no next."""
    result = s.schema.execute_sync(
        "{ postsConnection(first: 10) { pageInfo { hasNextPage endCursor } } }"
    )
    page = result.data["postsConnection"]["pageInfo"]
    cursor = page["endCursor"]

    # 100 posts / 10 per page = 10 pages; after the first we need 9 more iterations
    for _ in range(20):  # upper bound to avoid infinite loop in tests
        r = s.schema.execute_sync(
            f'{{ postsConnection(first: 10, after: "{cursor}") {{ pageInfo {{ hasNextPage endCursor }} }} }}'
        )
        page = r.data["postsConnection"]["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]

    assert not page["hasNextPage"]


def test_cursor_is_opaque_base64():
    """Cursors are base64-encoded and should round-trip correctly."""
    import base64
    result = s.schema.execute_sync(
        "{ postsConnection(first: 1) { edges { cursor node { id } } } }"
    )
    edge = result.data["postsConnection"]["edges"][0]
    cursor = edge["cursor"]
    post_id = edge["node"]["id"]

    # Cursor decodes to "post:<id>"
    decoded = base64.b64decode(cursor.encode()).decode()
    assert decoded == f"post:{post_id}"


def test_cursor_vs_offset_item_count():
    """Both methods return the same total count."""
    offset_result = s.schema.execute_sync("{ postsPage { total } }")
    cursor_result = s.schema.execute_sync("{ postsConnection { totalCount } }")
    assert offset_result.errors is None
    assert cursor_result.errors is None
    assert (
        offset_result.data["postsPage"]["total"]
        == cursor_result.data["postsConnection"]["totalCount"]
        == 100
    )
