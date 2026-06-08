"""
Marks
=====
Marks attach metadata to tests. pytest's built-in marks control execution
behaviour; custom marks let you create subsets you can filter with -m.

Built-in marks used here:
    skip        — always skip, with a required reason
    skipif      — skip conditionally (platform, version, env var, etc.)
    xfail       — expected to fail; XFAIL (expected) vs XPASS (unexpected)
    usefixtures — apply a fixture without declaring it as a parameter

Custom marks:
    Define any name you like. Register them in pytest.ini under `markers =`
    to suppress PytestUnknownMarkWarning and get them listed in --markers.

    Run only marked tests:
        pytest -m "slow"
        pytest -m "integration"
        pytest -m "not slow"
        pytest -m "slow and not integration"

Run:
    pytest 01_pytest_basics/test_04_marks.py -v
    pytest 01_pytest_basics/test_04_marks.py -v -m slow
    pytest 01_pytest_basics/test_04_marks.py -v -m "not slow"
"""

import sys
import pytest


# ---------------------------------------------------------------------------
# 1. skip — unconditionally skip
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason="Not implemented yet — tracked in issue #88")
def test_future_feature():
    # This body never runs. It exists as a placeholder so the test doesn't
    # get forgotten when the feature ships.
    assert False, "This should never execute"


# ---------------------------------------------------------------------------
# 2. skipif — skip based on a runtime condition
# ---------------------------------------------------------------------------

@pytest.mark.skipif(sys.platform == "win32", reason="Uses POSIX path conventions")
def test_unix_path_prefix():
    path = "/usr/local/bin/python"
    assert path.startswith("/")


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="structural pattern matching (match/case) requires Python 3.10+",
)
def test_match_statement():
    status = 200
    match status:
        case 200:
            label = "ok"
        case 404:
            label = "not_found"
        case _:
            label = "other"
    assert label == "ok"


# ---------------------------------------------------------------------------
# 3. xfail — document an expected failure
#
#    XFAIL: test fails as expected              → shown as 'x', suite passes
#    XPASS: test unexpectedly passes            → shown as 'X', suite passes
#    XPASS with strict=True                     → suite FAILS (good for CI)
#
#    Use xfail instead of deleting a test for a known bug: the mark
#    acts as a reminder, and if the bug is fixed it becomes XPASS so you
#    know to remove the mark.
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="Known float representation issue — see Python docs on IEEE 754")
def test_known_rounding_edge_case():
    # round(2.675, 2) should be 2.68 mathematically, but returns 2.67
    # because 2.675 cannot be represented exactly in binary floating point.
    assert round(2.675, 2) == 2.68


@pytest.mark.xfail(strict=True, reason="This assertion is deliberately wrong")
def test_strict_xfail_must_fail():
    # strict=True turns an unexpected pass into a test failure.
    # Use when you need CI to break the moment a known-broken thing starts working,
    # so you don't ship a fix without removing the xfail marker.
    assert 1 == 2


# ---------------------------------------------------------------------------
# 4. Custom marks for filtering
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_cpu_intensive_operation():
    total = sum(i * i for i in range(1_000_000))
    assert total > 0


@pytest.mark.slow
@pytest.mark.parametrize("n", [100_000, 200_000])
def test_slow_parametrized(n):
    assert sum(range(n)) > 0


def test_fast_calculation():
    assert 2 ** 10 == 1024


# ---------------------------------------------------------------------------
# 5. usefixtures mark — apply a fixture without a parameter
#    The fixture runs its setup/teardown, but its return value is discarded.
# ---------------------------------------------------------------------------

call_log: list[str] = []


@pytest.fixture
def log_test_name(request):
    call_log.append(f"start:{request.node.name}")
    yield
    call_log.append(f"end:{request.node.name}")


@pytest.mark.usefixtures("log_test_name")
def test_first_logged_test():
    assert True   # the fixture ran even though it's not a parameter


@pytest.mark.usefixtures("log_test_name")
def test_second_logged_test():
    assert True


def test_call_log_was_populated():
    # Both tests above ran the fixture; their names appear in the log.
    logged_names = {entry.split(":")[1] for entry in call_log}
    assert "test_first_logged_test" in logged_names
    assert "test_second_logged_test" in logged_names
