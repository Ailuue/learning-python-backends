"""
Tests for 02_relationships.

Key goal: prove that the naive resolver causes N+1 query calls,
then verify the query structure is correct before fixing it in section 03.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import data_02 as db
import schema as s


@pytest.fixture(autouse=True)
def reset_data():
    db.reset()
    yield
    db.reset()


# ── Basic queries ─────────────────────────────────────────────────────────────

def test_posts_returns_all_six():
    result = s.schema.execute_sync("{ posts { id title } }")
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["posts"]) == 6


def test_post_has_author_name():
    result = s.schema.execute_sync('{ post(id: "p1") { title author { name } } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["post"]["title"] == "Intro to CRDT"
    assert result.data["post"]["author"]["name"] == "Alice Nguyen"


def test_author_has_posts():
    result = s.schema.execute_sync('{ author(id: "a2") { name posts { title } } }')
    assert result.errors is None
    assert result.data is not None
    assert result.data["author"]["name"] == "Bob Okafor"
    assert len(result.data["author"]["posts"]) == 2


def test_author_id_not_exposed_in_schema():
    """author_id is Private — the client cannot request it."""
    result = s.schema.execute_sync("{ posts { author_id } }")
    assert result.errors is not None
    assert any("author_id" in str(e) for e in result.errors)


# ── N+1 demonstration ─────────────────────────────────────────────────────────

def test_posts_without_author_costs_zero_extra_queries():
    """No author field requested → no get_author calls."""
    result = s.schema.execute_sync("{ posts { title } }")
    assert result.errors is None
    assert result.data is not None
    # posts list fetch doesn't go through QueryCounter in our in-memory
    # setup, but no author lookups should happen
    assert db.QueryCounter.calls == 0


def test_n_plus_one_is_visible_when_requesting_author():
    """
    With 6 posts, querying { posts { author { name } } }
    fires 6 separate get_author calls — one per post.
    """
    db.QueryCounter.reset()
    result = s.schema.execute_sync("{ posts { title author { name } } }")
    assert result.errors is None
    assert result.data is not None
    assert len(result.data["posts"]) == 6
    # N+1: 6 individual get_author calls (duplicates included)
    assert db.QueryCounter.calls == 6


def test_three_authors_cause_six_author_lookups():
    """
    There are only 3 distinct authors, but with 6 posts we make 6 lookups —
    duplicates not de-duplicated without a DataLoader.
    """
    db.QueryCounter.reset()
    s.schema.execute_sync("{ posts { author { name } } }")
    # 6 posts × 1 author lookup each = 6, even though only 3 unique authors
    assert db.QueryCounter.calls == 6


def test_authors_with_posts_costs_one_query_per_author():
    """
    Querying authors with their posts: 1 get_posts_by_author per author = 3.
    """
    db.QueryCounter.reset()
    s.schema.execute_sync("{ authors { name posts { title } } }")
    assert db.QueryCounter.calls == 3


def test_single_post_costs_exactly_one_author_lookup():
    db.QueryCounter.reset()
    s.schema.execute_sync('{ post(id: "p1") { author { name } } }')
    assert db.QueryCounter.calls == 1
