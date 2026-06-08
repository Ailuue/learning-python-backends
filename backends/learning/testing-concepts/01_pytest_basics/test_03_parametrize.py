"""
Parametrize
===========
@pytest.mark.parametrize runs the same test function with multiple input sets.
It replaces copy-pasted test functions and makes the test matrix explicit.

Without parametrize you'd write:
    def test_even_2(): assert is_even(2)
    def test_even_4(): assert is_even(4)
    def test_odd_3():  assert not is_even(3)

With parametrize you write it once and declare the cases as data.
Each case appears as a separate entry in the test output so failures are
easy to locate.

Run:
    pytest 01_pytest_basics/test_03_parametrize.py -v
    # Notice how each case gets its own line in the output.
"""

import pytest


# ---------------------------------------------------------------------------
# Code under test
# ---------------------------------------------------------------------------

def is_even(n: int) -> bool:
    return n % 2 == 0


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def parse_positive_int(s: str) -> int:
    n = int(s)
    if n <= 0:
        raise ValueError(f"Expected positive integer, got {n}")
    return n


def normalize_email(email: str) -> str:
    return email.strip().lower()


# ---------------------------------------------------------------------------
# 1. Single-parameter parametrize
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [0, 2, 4, 100, -2, -100])
def test_even_numbers(n):
    assert is_even(n)


@pytest.mark.parametrize("n", [1, 3, 99, -1, -99])
def test_odd_numbers(n):
    assert not is_even(n)


# ---------------------------------------------------------------------------
# 2. Multiple parameters as a tuple
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("email, expected", [
    ("alice@example.com",     "alice@example.com"),
    ("ALICE@EXAMPLE.COM",     "alice@example.com"),
    ("  bob@example.com  ",   "bob@example.com"),
    ("Carol+Tag@Domain.ORG",  "carol+tag@domain.org"),
])
def test_normalize_email(email, expected):
    assert normalize_email(email) == expected


# ---------------------------------------------------------------------------
# 3. ids — give each case a descriptive name in the output
#    Default ids are just the parameter values; custom ids make failures
#    self-explanatory without reading the parameter list.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value, lo, hi, expected", [
    (5,   1, 10,  5),
    (0,   1, 10,  1),
    (15,  1, 10, 10),
    (1,   1, 10,  1),
    (10,  1, 10, 10),
], ids=["within_range", "below_min", "above_max", "at_min_boundary", "at_max_boundary"])
def test_clamp(value, lo, hi, expected):
    assert clamp(value, lo, hi) == expected


# ---------------------------------------------------------------------------
# 4. Parametrize with pytest.raises — testing multiple error inputs at once
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_input, expected_exc", [
    ("abc",  ValueError),   # not a number at all
    ("0",    ValueError),   # zero is not positive
    ("-5",   ValueError),   # negative
])
def test_parse_positive_int_rejects_invalid(bad_input, expected_exc):
    with pytest.raises(expected_exc):
        parse_positive_int(bad_input)


@pytest.mark.parametrize("good_input, expected", [
    ("1",    1),
    ("42",   42),
    ("999",  999),
])
def test_parse_positive_int_accepts_valid(good_input, expected):
    assert parse_positive_int(good_input) == expected


# ---------------------------------------------------------------------------
# 5. Stacked parametrize — cartesian product of all combinations
#    Two @parametrize decorators multiply: 2 × 3 = 6 test cases here.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("a", [0, 1])
@pytest.mark.parametrize("b", [10, 20, 30])
def test_sum_is_positive(a, b):
    # Runs 6 times: (0,10), (0,20), (0,30), (1,10), (1,20), (1,30)
    assert a + b > 0


# ---------------------------------------------------------------------------
# 6. pytest.param — attach marks or ids to individual cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n, expected", [
    pytest.param(2,  True,  id="small_even"),
    pytest.param(7,  False, id="small_odd"),
    pytest.param(10_000_000, True,  id="large_even", marks=pytest.mark.slow),
])
def test_is_even_with_marks(n, expected):
    assert is_even(n) == expected
