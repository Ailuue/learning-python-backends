"""
Tests for 03_dataloaders.

Key goal: prove that using a DataLoader reduces N+1 to a single batch call.
Compare the call counts against section 02 results.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import data_03 as db
import schema as s
from loaders_03 import make_author_loader


@pytest.fixture(autouse=True)
def reset_data():
    db.reset()
    yield
    db.reset()


def fresh_context() -> dict:
    return {"author_loader": make_author_loader()}


# ── Correctness (same results as section 02) ─────────────────────────────────

async def test_posts_with_authors_returns_correct_data():
    result = await s.schema.execute(
        "{ posts { title author { name } } }",
        context_value=fresh_context(),
    )
    assert result.errors is None
    posts = result.data["posts"]
    assert len(posts) == 6
    assert posts[0]["author"]["name"] == "Alice Nguyen"
    assert posts[2]["author"]["name"] == "Bob Okafor"


async def test_single_post_author_resolved_correctly():
    result = await s.schema.execute(
        '{ post(id: "p3") { title author { name } } }',
        context_value=fresh_context(),
    )
    assert result.errors is None
    assert result.data["post"]["author"]["name"] == "Bob Okafor"


# ── N+1 is gone: 6 posts → 1 batch call ─────────────────────────────────────

async def test_six_posts_cause_only_one_batch_author_load():
    """
    THE key test: N posts → 1 DB call, not N.
    In section 02, this would be 6 calls. With DataLoader: 1.
    """
    result = await s.schema.execute(
        "{ posts { title author { name } } }",
        context_value=fresh_context(),
    )
    assert result.errors is None
    assert db.BatchCounter.calls == 1


async def test_posts_without_author_field_makes_zero_batch_calls():
    result = await s.schema.execute(
        "{ posts { title } }",
        context_value=fresh_context(),
    )
    assert result.errors is None
    assert db.BatchCounter.calls == 0


async def test_two_posts_same_author_still_only_one_batch_call():
    """
    Posts p1 and p2 both have author_id="a1".
    DataLoader caches the result — batch fires once, not twice.
    """
    result = await s.schema.execute(
        '{ posts { author { name } } }',
        context_value=fresh_context(),
    )
    assert result.errors is None
    assert db.BatchCounter.calls == 1


async def test_single_post_costs_one_batch_call():
    result = await s.schema.execute(
        '{ post(id: "p1") { author { name } } }',
        context_value=fresh_context(),
    )
    assert result.errors is None
    assert db.BatchCounter.calls == 1


# ── Each request gets a fresh loader (no cross-request cache) ─────────────────

async def test_two_separate_requests_each_make_one_batch_call():
    """
    Fresh loader per request means no stale cache across requests.
    Each request fires exactly one batch call independently.
    """
    ctx1 = fresh_context()
    await s.schema.execute("{ posts { author { name } } }", context_value=ctx1)
    calls_after_first = db.BatchCounter.calls
    assert calls_after_first == 1

    ctx2 = fresh_context()
    await s.schema.execute("{ posts { author { name } } }", context_value=ctx2)
    assert db.BatchCounter.calls == 2  # second request fired its own batch
