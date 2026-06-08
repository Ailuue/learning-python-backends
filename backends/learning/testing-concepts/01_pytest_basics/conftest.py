"""
conftest.py
===========
Fixtures defined here are automatically visible to every test file in this
directory and any subdirectories — no import required.

pytest loads conftest.py files bottom-up from the rootdir to the test file,
merging the fixture namespaces. A fixture in a subdirectory conftest.py
overrides one with the same name from a parent conftest.py.

Use conftest.py for:
  - Fixtures shared across multiple test files
  - Pytest hooks (pytest_configure, pytest_collection_modifyitems, etc.)
  - Registering custom marks (to avoid PytestUnknownMarkWarning)
"""
import pytest


@pytest.fixture
def app_config():
    """
    Available to all test files in this directory without any import.
    Change the value here once to affect every test that uses it.
    """
    return {
        "api_url": "http://localhost:8000",
        "timeout": 30,
        "retries": 3,
    }
