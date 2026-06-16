# The tests in this folder use a script-style harness (each file runs on import
# and prints "N passed, M failed") rather than pytest. Tell pytest to skip
# collecting them so `pytest` here reports nothing to do instead of erroring on
# the harness's `test(...)` helpers. Run them with `python run_tests.py` instead.
collect_ignore_glob = ["**/test_*.py"]
