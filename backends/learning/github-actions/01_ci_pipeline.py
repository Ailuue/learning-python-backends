"""
CI Pipeline — .github/workflows/ci.yml
========================================

CONCEPTS:
  1. Why CI matters — the "works on my machine" problem
  2. Workflow anatomy: on, jobs, steps, uses vs run
  3. Path filters — only running when relevant files change
  4. concurrency — cancelling stale runs
  5. Matrix strategy — testing across multiple Python versions
  6. fail-fast: false — seeing the full compatibility picture
  7. Pip caching — making repeated runs fast
  8. Separating lint from test — fast feedback, no wasted compute
  9. Artifacts — persisting failure output for investigation
  10. Status checks — blocking merges until CI passes

--- WHY CI? ---

"Works on my machine" is not a guarantee. CI runs your code in a
clean, reproducible environment — the same every time, for everyone.
A PR that breaks tests on Python 3.11 but not 3.13 will fail CI
before it merges, not after it ships.

The goal: make the main branch always deployable.

--- WORKFLOW ANATOMY ---

on:                         Trigger — what causes this workflow to run
  push:
    branches: [main]        Only on pushes to main (not feature branches)
    paths:                  Only when these paths change
      - "src/**"

jobs:                       Parallel containers by default
  build:                    Job name (arbitrary)
    runs-on: ubuntu-latest  Which runner OS to use
    steps:                  Sequential commands within a job
      - uses: ...           Run a pre-built Action from the marketplace
      - run: ...            Run a shell command directly

--- PATH FILTERS ---

Without path filters, every push to ANY file triggers the workflow.
That means pushing a README edit runs the full test suite.

paths filter: only trigger when files matching these globs changed.

    on:
      push:
        paths:
          - "backends/learning/testing-concepts/**"
          - ".github/workflows/ci.yml"

Including the workflow file itself is important: if you change the CI
config, you want CI to re-run against the new config immediately.

--- CONCURRENCY ---

If you push three times in quick succession, you don't want three
parallel CI runs — the first two are stale by the time they finish.

    concurrency:
      group: ci-${{ github.ref }}
      cancel-in-progress: true

group: a key that identifies "runs of the same thing".
  Using github.ref means separate concurrency per branch.
  Two PRs can run CI in parallel; only the latest push to the same
  branch cancels the previous one.

cancel-in-progress: true cancels any running job in the same group
  when a new one starts. Without this, you just queue behind the old run.

--- MATRIX STRATEGY ---

A single job config run multiple times with different variable values.

    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]

This creates three parallel jobs. GitHub allocates three runners simultaneously.
Each job gets a different value of matrix.python-version.

Reference the value with: ${{ matrix.python-version }}

Total runner minutes = (time per job) × (number of matrix entries).
Three 2-minute jobs = 6 minutes billed (but wall-clock time is ~2 minutes
because they run in parallel).

--- fail-fast: false ---

Default behavior (fail-fast: true): if Python 3.11 fails, cancel 3.12 and 3.13.
You see one failure and have no idea about the other versions.

fail-fast: false: all matrix entries run to completion, even if one fails.
You get the full compatibility matrix in a single run.

    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
      fail-fast: false

Always use fail-fast: false unless you want to save compute on disposable branches.

--- PIP CACHING ---

Without caching, every run downloads all packages from PyPI from scratch.
For a project with 20 dependencies, that's 200–500 MB and 30–60 seconds
of network I/O on every run.

    - uses: actions/cache@v4
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ matrix.python-version }}-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-${{ matrix.python-version }}-

key: the full cache key. If this key exists, the cache is restored exactly.
restore-keys: fallback prefix. If the exact key doesn't exist (requirements.txt
  changed), fall back to the most recent cache for this OS+Python combination.
  pip will still re-download the changed packages but reuses everything else.

hashFiles('requirements.txt'): a hash of the file contents.
  Cache is automatically invalidated when requirements.txt changes.

Note: caching pip's DOWNLOAD cache (~/.cache/pip), not the site-packages.
  The download cache stores wheels (.whl files). pip still installs from
  the cached wheel without re-downloading, but pip install itself still runs.
  This approach is simpler than caching the entire venv.

--- SEPARATING LINT FROM TEST ---

    jobs:
      lint:
        ...   (runs first, fast, on a single Python version)
      test:
        ...   (runs in parallel with lint, on the matrix)

Lint and test run in parallel. If formatting is wrong, you see the lint
failure within 20 seconds — you don't wait for the 3-minute test matrix
to tell you there's a one-character formatting error.

Keeping them separate also means: fix a lint error → only lint re-runs
(if you use path-scoped caching), not the whole matrix.

--- ARTIFACTS ---

When a test fails, the default runner output shows the pytest summary.
But sometimes you want the raw output, especially for flaky tests or
tests that generate files (coverage reports, screenshots, logs).

    - uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: test-results-${{ matrix.python-version }}
        path: .pytest_cache/
        retention-days: 7

if: failure() — only upload when the previous step failed.
retention-days: 7 — auto-delete after 7 days (max 90 days, default 90).
name: unique per matrix entry so 3.11 and 3.12 results don't overwrite each other.

Download artifacts:
  GitHub UI → run → Artifacts section, or:
  gh run download <run-id> --name test-results-3.11

--- STATUS CHECKS AND BRANCH PROTECTION ---

After CI is working, add branch protection rules (repo Settings → Branches):
  - Require status checks to pass before merging
  - Select the job names from your workflow (e.g. "Lint", "Test / Python 3.13")
  - Optionally require all matrix entries (3.11, 3.12, 3.13)

Now PRs can't be merged until CI is green. main stays deployable.

--- EXERCISES ---

1. Watch ci.yml run:
     git add .github/workflows/ci.yml
     git commit -m "ci: add test pipeline"
     git push
   Open: https://github.com/<your-repo>/actions

2. Observe path filtering:
   Edit a file NOT in testing-concepts/ (e.g. README.md) and push.
   ci.yml should NOT trigger. Edit a file in testing-concepts/ and push.
   ci.yml SHOULD trigger.

3. Observe concurrency cancellation:
   Push two commits in rapid succession. Check the Actions tab —
   the first run should show "Cancelled" as the second run starts.

4. Break a test and see the matrix:
   Add `assert False` to one test file. Push. Observe that all three
   Python version jobs run (fail-fast: false) and all three fail.
   Fix the test and push again.

5. Add a branch protection rule:
   Repo Settings → Branches → Add rule → Require status checks.
   Try creating a PR with a failing test. It should be blocked from merging.
"""

# Summary of key workflow configuration patterns
CI_PATTERNS = {
    "path_filter":      "Only trigger when specific files change",
    "concurrency":      "Cancel stale runs; only latest push matters",
    "matrix":           "Test across multiple Python versions in parallel",
    "fail_fast_false":  "See full compatibility matrix even when one version fails",
    "pip_cache":        "Cache wheels to avoid re-downloading on every run",
    "separate_jobs":    "Lint fast, test slow — parallel + independent failure signals",
    "artifacts":        "Upload test output on failure for post-mortem investigation",
    "status_checks":    "Block PR merges until CI is green",
}

# Cron quick reference
CRON_SYNTAX = """
┌──────────── minute        (0-59)
│ ┌────────── hour          (0-23, UTC)
│ │ ┌──────── day of month  (1-31)
│ │ │ ┌────── month         (1-12)
│ │ │ │ ┌──── day of week   (0-6, 0=Sunday)
│ │ │ │ │
* * * * *

Examples:
  "0 9 * * 1"    → every Monday at 09:00 UTC
  "0 */6 * * *"  → every 6 hours
  "30 2 1 * *"   → 1st of every month at 02:30 UTC
  "0 0 * * *"    → daily at midnight UTC
"""
