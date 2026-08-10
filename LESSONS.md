# Lessons

## 2026-08-10 — Demo scripts default to a `postgres` role this machine doesn't have

**Expected:** run any `database-concepts` demo directly after `pg_isready` came back green.

**What happened:** every psycopg2/asyncpg demo failed with
`role "postgres" does not exist`. The Homebrew Postgres install creates a role
named after the OS user, not `postgres`, but the demos hardcode
`postgres:postgres` as the fallback when `DATABASE_URL` / `DB_USER` are unset.

**Next time:** export the overrides before running anything under
`database-concepts` or `backend-concepts`:

```bash
export DB_USER=alex DB_PASSWORD=
# or, for the ones that read a single URL:
export DATABASE_URL="postgresql+asyncpg://alex@localhost:5432/<dbname>"
```

The databases themselves also have to exist first — `createdb async_pool_demo`,
`transactions_demo`, `n_plus_one_demo`, `caching_demo`. A `.env` per project
directory would remove this friction permanently.

## 2026-08-10 — mypy has never actually run in this repo

**Expected:** `mypy.ini` at the root with `disallow_untyped_defs = true` meant
mypy was enforcing something.

**What happened:** it aborts before checking a single file —
`Duplicate module named "handler"` — because the flat one-folder-per-concept
layout produces colliding module names (12 `main.py`, 12 `conftest.py`, 8
`db.py`). `--explicit-package-bases` does not help; the duplicates share a base.

**Next time:** don't assume a config file at the root means the tool runs.

**Resolved:** `mypy.ini` is gone (`5fced02`). Before removing it I measured what
it was actually asking for — turning on pyright's nearest equivalent,
`reportMissingParameterType`, produces **517 warnings** against the current
tree, nearly all of them demo functions that are deliberately untyped. So
`disallow_untyped_defs = true` was never a rule this repo followed; it was a
rule that never ran. One checker (pyright, which is what Pylance uses anyway)
beats two that disagree.

## 2026-08-10 — Generating protobuf stubs made Pylance *worse*, not better

**Expected:** running `grpc-concepts/generate_protos.sh` would clear the 12
unresolved `greeter_pb2` / `stock_pb2` imports.

**What happened:** it cleared those 12 and introduced ~70 new ones —
`"HelloReply" is not a known attribute of module "greeter_pb2"`. The generated
`*_pb2.py` doesn't declare its message classes; it builds them at runtime
through `_builder.BuildTopDescriptorsAndMessages`, so there is nothing for a
static checker to see.

**Next time:** always pass `--pyi_out` alongside `--python_out`. The `.pyi`
stubs are what make generated protobuf code legible to Pylance, and protoc will
not emit them unless asked. Fixed in `07daf6a`; the generated files are now
gitignored and excluded from pyright, since they are build output.

## 2026-08-10 — A metrics bug that only a counter delta could prove

**Expected:** reading the middleware would be enough to confirm the
double-count in `observability/02_metrics.py`.

**What happened:** reading it strongly suggested the bug (the `except` branch
and the `finally` branch both incremented `ERROR_COUNT`), but "strongly
suggested" is not proof, and the fix changed control flow — dropping the
`except` branch entirely and relying on the implicit re-raise.

**Next time:** for observability code, assert on the counter itself. Driving one
failing request through `TestClient(raise_server_exceptions=False)` and diffing
`COUNTER.labels(...)._value.get()` gave a hard before/after — 2.0 against the
old commit, 1.0 against the new one — in about ten lines. Worth doing whenever a
fix claims "this was being counted twice."
