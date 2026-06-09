"""
Tests for 04_types: enums, unions, interfaces, custom scalars.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import schema as s


def test_enum_field_serializes_correctly():
    result = s.schema.execute_sync('{ article(id: "a1") { genre status } }')
    assert result.errors is None
    assert result.data["article"]["genre"] == "NON_FICTION"
    assert result.data["article"]["status"] == "PUBLISHED"


def test_enum_filters_articles_by_genre():
    result = s.schema.execute_sync("{ articlesByGenre(genre: NON_FICTION) { title } }")
    assert result.errors is None
    assert result.data["articlesByGenre"][0]["title"] == "GraphQL Basics"


def test_invalid_enum_value_causes_error():
    result = s.schema.execute_sync("{ articlesByGenre(genre: ROMANCE) { title } }")
    assert result.errors is not None


def test_custom_scalar_date_serializes_to_iso_string():
    result = s.schema.execute_sync('{ article(id: "a1") { publishedAt } }')
    assert result.errors is None
    assert result.data["article"]["publishedAt"] == "2024-01-15"


def test_nullable_date_can_be_null():
    result = s.schema.execute_sync('{ article(id: "a2") { publishedAt } }')
    assert result.errors is None
    assert result.data["article"]["publishedAt"] is None


def test_union_search_returns_mixed_types():
    result = s.schema.execute_sync("""
        {
          search(term: "intro") {
            __typename
            ... on Article { title body }
            ... on Video   { title url }
          }
        }
    """)
    assert result.errors is None
    results = result.data["search"]
    type_names = {r["__typename"] for r in results}
    assert "Video" in type_names


def test_union_search_articles_only():
    result = s.schema.execute_sync("""
        {
          search(term: "GraphQL") {
            __typename
            ... on Article { title }
          }
        }
    """)
    assert result.errors is None
    assert result.data["search"][0]["__typename"] == "Article"
    assert result.data["search"][0]["title"] == "GraphQL Basics"


def test_published_content_filters_by_status():
    result = s.schema.execute_sync("""
        {
          publishedContent {
            __typename
            ... on Article { title status }
            ... on Video   { title status }
          }
        }
    """)
    assert result.errors is None
    for item in result.data["publishedContent"]:
        assert item["status"] == "PUBLISHED"


def test_interface_fields_accessible_without_fragment():
    """Shared interface fields (title, status) are available on all types."""
    result = s.schema.execute_sync("{ articles { title status } }")
    assert result.errors is None
    assert result.data["articles"][0]["title"] == "GraphQL Basics"


def test_typename_in_union_result():
    result = s.schema.execute_sync("""
        { publishedContent { __typename } }
    """)
    assert result.errors is None
    type_names = {r["__typename"] for r in result.data["publishedContent"]}
    assert "Article" in type_names
    assert "Video" in type_names
