#!/usr/bin/env python3
"""
Run every data-structures-and-algorithms test in one command.

These tests use a lightweight script-style harness (each prints
"N passed, M failed" and runs on import) rather than pytest, so this
script discovers each `test_*.py`, runs it in its own directory — they
import sibling modules by name — and reports an overall pass/fail.

Usage:
    python run_tests.py          # run everything
    python run_tests.py sorting  # only paths containing "sorting"
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COUNT_RE = re.compile(r"(\d+)\s+passed,\s+(\d+)\s+failed")


def run_one(test_file: Path) -> tuple[bool, str]:
    """Return (ok, summary) for a single test file."""
    proc = subprocess.run(
        [sys.executable, test_file.name],
        cwd=test_file.parent,
        capture_output=True,
        text=True,
    )
    output = proc.stdout + proc.stderr

    if proc.returncode != 0:
        return False, "crashed (non-zero exit / traceback)"

    matches = COUNT_RE.findall(output)
    if not matches:
        return False, "no pass/fail summary found in output"

    total_passed = sum(int(p) for p, _ in matches)
    total_failed = sum(int(f) for _, f in matches)
    summary = f"{total_passed} passed, {total_failed} failed"
    return total_failed == 0, summary


def main() -> int:
    needle = sys.argv[1] if len(sys.argv) > 1 else ""
    test_files = sorted(
        f for f in ROOT.rglob("test_*.py") if needle in str(f.relative_to(ROOT))
    )

    if not test_files:
        print(f"No test files matched {needle!r}.")
        return 1

    failures = []
    for test_file in test_files:
        rel = test_file.relative_to(ROOT)
        ok, summary = run_one(test_file)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {rel}  ({summary})")
        if not ok:
            failures.append(rel)

    print("-" * 60)
    if failures:
        print(f"{len(failures)} file(s) FAILED:")
        for rel in failures:
            print(f"  - {rel}")
        return 1
    print(f"All {len(test_files)} test files passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
