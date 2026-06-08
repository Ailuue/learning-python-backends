"""
pytest Basics
=============
pytest discovers tests by scanning for files named test_*.py or *_test.py,
then collecting functions and methods whose names start with test_.

The key difference from unittest: plain `assert` statements produce rich
failure messages. pytest rewrites the bytecode at import time to capture the
actual values on both sides of the comparison — no assertEqual, assertTrue,
or other helper methods needed.

Test discovery rules:
    - File:     test_*.py or *_test.py
    - Function: starts with test_
    - Class:    starts with Test  (no __init__)
    - Method:   starts with test_

Run:
    pytest 01_pytest_basics/test_01_basics.py -v
"""

import pytest


# ---------------------------------------------------------------------------
# Code under test
# ---------------------------------------------------------------------------

def add(a: int, b: int) -> int:
    return a + b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


def slugify(text: str) -> str:
    return text.lower().strip().replace(" ", "-")


# ---------------------------------------------------------------------------
# 1. Basic test functions
# ---------------------------------------------------------------------------

def test_add_two_positives():
    assert add(2, 3) == 5


def test_add_negative_numbers():
    assert add(-1, -2) == -3


def test_add_with_zero():
    assert add(0, 99) == 99


def test_slugify_lowercases():
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_whitespace():
    assert slugify("  spaces  ") == "spaces"


# ---------------------------------------------------------------------------
# 2. Assertion rewriting — failures print the actual values
#    Uncomment the assert below and run to see pytest's diff output.
# ---------------------------------------------------------------------------

def test_list_has_expected_items():
    items = ["apple", "banana", "cherry"]
    assert "banana" in items
    assert len(items) == 3
    # assert "mango" in items   # ← uncomment to see: AssertionError: assert 'mango' in ['apple', ...]


def test_dict_contains_key():
    user = {"id": 1, "name": "Alice", "role": "admin"}
    assert user["role"] == "admin"
    assert "email" not in user   # key absent


# ---------------------------------------------------------------------------
# 3. Testing exceptions with pytest.raises
# ---------------------------------------------------------------------------

def test_divide_by_zero_raises_value_error():
    with pytest.raises(ValueError):
        divide(10, 0)


def test_exception_message_matches():
    # match= accepts a regex pattern — checked against str(exception)
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)


def test_exception_object_is_accessible():
    with pytest.raises(ValueError) as exc_info:
        divide(5, 0)
    # exc_info.value is the actual exception object
    assert "zero" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# 4. Grouping tests with classes
#    No __init__, no inheritance — just a namespace for related tests.
# ---------------------------------------------------------------------------

class TestDivide:
    def test_even_division(self):
        assert divide(10, 2) == 5.0

    def test_negative_divisor(self):
        assert divide(10, -2) == -5.0

    def test_fractional_result(self):
        result = divide(1, 3)
        assert pytest.approx(result, rel=1e-3) == 0.333


# ---------------------------------------------------------------------------
# 5. pytest.approx for floating-point comparisons
#    0.1 + 0.2 is not exactly 0.3 in IEEE 754 — approx handles the tolerance.
# ---------------------------------------------------------------------------

def test_float_addition():
    assert 0.1 + 0.2 == pytest.approx(0.3)


def test_approx_absolute_tolerance():
    assert 1.001 == pytest.approx(1.0, abs=0.01)


def test_approx_relative_tolerance():
    assert 100.5 == pytest.approx(100.0, rel=0.01)  # within 1%


def test_approx_list_of_floats():
    results = [divide(1, 3), divide(2, 3)]
    assert results == pytest.approx([0.333, 0.667], rel=1e-2)
