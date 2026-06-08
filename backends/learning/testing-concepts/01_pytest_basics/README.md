# pytest Basics

## What is this?

pytest discovers and runs tests automatically — no boilerplate, no class required, just functions that start with `test_`. Its most powerful feature is **assertion rewriting**: pytest rewrites plain `assert` statements at import time so failures print the actual values, not just `AssertionError`.

The four files here cover the fundamentals in the order you'd encounter them while building a real test suite.

## What the files cover

| File | What it teaches |
|---|---|
| `test_01_basics.py` | Test functions, assertion rewriting, `pytest.raises`, class grouping, `pytest.approx` |
| `test_02_fixtures.py` | Fixtures, `yield` for teardown, scope (`function`/`module`/`session`), fixture composition |
| `test_03_parametrize.py` | `@pytest.mark.parametrize`, readable `ids`, stacked parametrize for cartesian products |
| `test_04_marks.py` | `skip`, `skipif`, `xfail`, custom marks for filtering with `-m` |

`conftest.py` shows where to put shared fixtures so they're available to every file without importing.

## How to run

```bash
# From the testing-concepts/ root
pytest 01_pytest_basics/ -v

# Run just one file
pytest 01_pytest_basics/test_02_fixtures.py -v

# Run only tests tagged with a custom mark
pytest 01_pytest_basics/ -v -m "slow"
pytest 01_pytest_basics/ -v -m "not slow"
```
