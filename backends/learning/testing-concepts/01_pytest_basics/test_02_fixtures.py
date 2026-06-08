"""
Fixtures
========
A fixture is a function that provides a value or resource to a test.
pytest injects it by matching the parameter name — the test just declares
what it needs. No setup/teardown classes, no manual wiring.

Fixtures solve three problems:
  1. Reuse: define setup logic once, use it in many tests
  2. Composition: fixtures can depend on other fixtures
  3. Cleanup: yield-fixtures run teardown code even when tests fail

Scope controls how often a fixture is created and destroyed:

    function  (default) — new instance per test function
    class               — shared within one test class
    module              — shared within one test file
    session             — shared for the entire pytest run

A wider-scope fixture must not depend on a narrower-scope one
(e.g. a session fixture cannot request a function-scoped fixture).

Run:
    pytest 01_pytest_basics/test_02_fixtures.py -v -s
    # -s shows print output so you can observe scope lifecycle
"""

import pytest


# ---------------------------------------------------------------------------
# 1. Basic fixture — provides a value to the test
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user():
    return {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "user"}


def test_user_has_name(sample_user):
    assert sample_user["name"] == "Alice"


def test_user_default_role(sample_user):
    assert sample_user["role"] == "user"


# Two tests that both use the fixture get independent copies (function scope).
def test_mutation_does_not_bleed(sample_user):
    sample_user["role"] = "admin"   # mutate the copy
    assert sample_user["role"] == "admin"


def test_original_role_is_unaffected(sample_user):
    # A fresh fixture is injected — the mutation above is not visible here.
    assert sample_user["role"] == "user"


# ---------------------------------------------------------------------------
# 2. yield fixture — setup before yield, teardown after
#    Runs teardown even if the test raises an exception.
# ---------------------------------------------------------------------------

@pytest.fixture
def tracked_list():
    items = []               # setup
    yield items              # test receives `items`
    items.clear()            # teardown — runs after the test completes
    print(f"\n  [teardown] tracked_list cleared")


def test_append_items(tracked_list):
    tracked_list.append("a")
    tracked_list.append("b")
    assert len(tracked_list) == 2


def test_list_starts_empty_again(tracked_list):
    # Each call to the fixture produces a new empty list.
    assert tracked_list == []


# ---------------------------------------------------------------------------
# 3. Scope — module scope shares one instance across an entire file
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def shared_counter():
    print("\n  [setup] shared_counter created")
    state = {"count": 0}
    yield state
    print(f"\n  [teardown] shared_counter final count={state['count']}")


def test_counter_first_use(shared_counter):
    shared_counter["count"] += 1
    assert shared_counter["count"] == 1


def test_counter_second_use(shared_counter):
    # Same object — carries over within module scope.
    shared_counter["count"] += 1
    assert shared_counter["count"] == 2


# ---------------------------------------------------------------------------
# 4. Fixture composition — fixtures can depend on other fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user(sample_user):
    # Build on top of sample_user — don't duplicate its setup.
    sample_user["role"] = "admin"
    sample_user["permissions"] = ["read", "write", "delete"]
    return sample_user


def test_admin_has_correct_role(admin_user):
    assert admin_user["role"] == "admin"


def test_admin_has_permissions(admin_user):
    assert "delete" in admin_user["permissions"]


def test_admin_still_has_email(admin_user):
    # Properties from sample_user are inherited.
    assert admin_user["email"] == "alice@example.com"


# ---------------------------------------------------------------------------
# 5. Parametrized fixtures — run every dependent test once per param value
# ---------------------------------------------------------------------------

@pytest.fixture(params=["alice@example.com", "BOB@EXAMPLE.COM", "carol+tag@domain.co"])
def raw_email(request):
    # request.param holds the current value in the parametrize loop.
    return request.param


def test_email_contains_at_sign(raw_email):
    # This test runs three times — once for each email address.
    assert "@" in raw_email


# ---------------------------------------------------------------------------
# 6. The request fixture — access fixture metadata inside a fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def unique_name(request):
    # request.node.name is the full test node id (useful for unique data).
    return f"object-for-{request.node.name}"


def test_fixture_knows_its_test_name(unique_name):
    assert "test_fixture_knows_its_test_name" in unique_name


# ---------------------------------------------------------------------------
# 7. autouse — apply a fixture to every test in scope without declaring it
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_global_state():
    """Runs before and after every test in this file, no opt-in needed."""
    # setup: nothing to do here
    yield
    # teardown: nothing to clean in this example, but the pattern is real —
    # useful for clearing caches, resetting singletons, or flushing fakes.
