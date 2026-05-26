"""
Development Workflow
=====================

CONCEPTS:
  1. Hot-reload: how bind mount + uvicorn --reload actually work
  2. Running tests inside containers: exec vs run, test compose override
  3. Docker build cache: layer cache + BuildKit cache mounts + CI caching
  4. Request tracing: follow one request across service logs with an ID
  5. docker compose logs -f: multi-service log filtering and grepping

CHANGES IN THIS SESSION:
  app/main.py              added request ID middleware + logging
  app/requirements.txt     added pytest + httpx
  app/tests/test_api.py    integration test suite
  Dockerfile               BuildKit syntax + pip cache mount
  docker-compose.test.yml  test runner override

--- HOT-RELOAD ---

The setup (already in docker-compose.override.yml):
  volumes:
    - ./app:/app           ← bind mount: your host files live in the container
  command: [..., "--reload"]   ← uvicorn watches for file changes

How it works:
  1. The bind mount makes your host's ./app directory appear at /app inside
     the container. No COPY step — it's a live shared filesystem view.
  2. uvicorn uses the watchfiles library to watch /app for file system events.
  3. When you save a .py file on your Mac, the event propagates through
     Docker Desktop's filesystem layer to the container.
  4. watchfiles detects the change, uvicorn gracefully restarts the worker.
  5. Your next request hits the updated code, typically within 1-2 seconds.

Mac/Docker Desktop caveat:
  Docker Desktop on Mac runs containers in a Linux VM. File system events
  (inotify) don't propagate perfectly through the VM layer. If hot-reload
  feels slow or misses changes, force polling mode:
    environment:
      WATCHFILES_FORCE_POLLING: "true"   ← add to app in docker-compose.override.yml
  Polling is slightly less efficient but reliable across all platforms.

Never use --reload in production:
  - --reload keeps a file watcher process running permanently
  - uvicorn uses more memory and restarts on any file change (including logs,
    .pyc files, etc. if not excluded)
  - The restart causes a brief window where requests are dropped

The bind mount is the key: without it, the container has a snapshot of
your code from the last `docker compose build`. With it, the container
sees your live filesystem in real time.

--- RUNNING TESTS INSIDE CONTAINERS ---

Three approaches, each with different trade-offs:

  1. docker compose exec app python -m pytest tests/ -v
     ─────────────────────────────────────────────────────
     Runs pytest inside the ALREADY-RUNNING dev container.
     The bind mount is active, so tests see your latest code (unsaved changes
     included via OS buffer — save first to be sure).
     DB and Redis are reachable because the container is already wired up.
     Fast: no startup time.
     Requires: docker compose up is already running.

  2. docker compose run --rm app python -m pytest tests/ -v
     ─────────────────────────────────────────────────────
     Spins up a FRESH container using the override (bind mount active).
     `depends_on` is respected — db and redis start first and wait for
     their health checks before pytest runs.
     Slower: full container startup, health check wait.
     Use when: you want a clean environment without other processes running.

  3. docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app
     ─────────────────────────────────────────────────────
     Uses the test override file. docker-compose.override.yml is NOT
     auto-applied (because you're explicitly specifying files with -f).
     Tests run against the BUILT IMAGE — no bind mount. This is what CI does.
     Use when: verifying the image behaves correctly, not just your local code.

The difference between 2 and 3:
  Run 2 with live code changes but before rebuilding the image.
  Run 3 after rebuilding to verify the image (what ships) is correct.

Adding tests to CI (GitHub Actions sketch):
  jobs:
    test:
      steps:
        - run: docker compose build
        - run: docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app

--- DOCKER BUILD CACHE ---

Two separate caching mechanisms — easy to confuse:

MECHANISM 1: Layer cache (always available, no BuildKit needed)
  Docker caches each Dockerfile instruction as a layer.
  If the instruction and all its inputs are unchanged, the cached layer is reused.
  We already covered this: copy requirements.txt before app code so the pip
  install layer is not re-run on every code change.

MECHANISM 2: BuildKit cache mounts (declared with --mount=type=cache)
  A persistent cache volume that exists OUTSIDE the image layers.
  Survives between builds. Never bloats the image.
  Declared in the Dockerfile (now updated with # syntax=docker/dockerfile:1):

    RUN --mount=type=cache,target=/root/.cache/pip \
        pip install -r requirements.txt

  pip stores its download cache at /root/.cache/pip. Normally discarded
  between builds. With the cache mount, it persists on the build host.
  Second build: pip finds cached wheels and skips re-downloading.
  Time saved: significant for large packages (numpy, torch, etc.)

  Requires BuildKit (default in Docker 23+, Docker Desktop always).
  The # syntax=docker/dockerfile:1 directive on line 1 of Dockerfile
  explicitly opts in to the latest BuildKit frontend features.

CI CACHING (GitHub Actions / GitLab CI):
  The BuildKit cache mount only helps on the SAME machine between builds.
  In CI, every run gets a fresh runner. Use registry-based caching instead:

  # Push cache to the registry after build
  docker buildx build \
    --cache-to type=registry,ref=ghcr.io/user/myapp:cache,mode=max \
    --cache-from type=registry,ref=ghcr.io/user/myapp:cache \
    -t myapp:latest .

  The CI runner pulls the cache from the registry, uses it for the build,
  then pushes the updated cache back. Next CI run pulls the fresh cache.
  mode=max caches ALL layers; mode=min (default) only the final stage.

Watch the cache in action:
  docker compose build        # first build — all layers fresh
  # (change a line in app/main.py)
  docker compose build        # second build — pip install should be CACHED
  # Output: => CACHED [builder 5/5] RUN --mount=type=cache...  0.0s

--- REQUEST TRACING ---

The middleware added to app/main.py generates a request_id for every request:
  - Logged on every request: "request_id=ab12cd34 method=GET path=/items status=200"
  - Returned in the X-Request-ID response header

Why this matters in multi-service systems:
  Without IDs, logs from concurrent requests intermix and become impossible
  to follow. With an ID, you can grep all log lines for one specific request
  even across multiple services.

Practice session:

  # 1. Start with logs following all services
  docker compose logs -f

  # 2. In another terminal, make some requests
  curl http://localhost:8000/items
  curl -X POST http://localhost:8000/items -H 'Content-Type: application/json' -d '{"name": "trace-test"}'

  # 3. Back in the logs terminal — find the request IDs in the app output
  # Something like: 2024-01-15 10:23:45 INFO request_id=ab12cd34 method=GET path=/items status=200

  # 4. Grep all logs for that specific request ID
  docker compose logs | grep ab12cd34
  # All log lines related to that one request, even across service restarts

  # 5. Check the response header
  curl -v http://localhost:8000/ 2>&1 | grep -i x-request-id

Propagating the ID across services:
  In a real system: when your app calls another service, include the ID:
    headers = {"X-Request-ID": request_id}
    requests.get("http://other-service/api", headers=headers)
  The downstream service reads that header and uses it in its own logs.
  One ID now traces the full chain: gateway → app → db → cache → downstream.

--- docker compose logs — MULTI-SERVICE ---

  # Follow all services together (color-coded by service name in terminal)
  docker compose logs -f

  # Follow specific services only
  docker compose logs -f app
  docker compose logs -f app db
  docker compose logs -f app db redis

  # Last N lines from all services
  docker compose logs --tail 50

  # Last N lines from one service
  docker compose logs --tail 20 app

  # With Docker's timestamps (separate from your app's own log timestamps)
  docker compose logs -t
  docker compose logs -tf app

  # From a time ago (relative)
  docker compose logs --since 5m app
  docker compose logs --since 2m db redis

  # Combine: last 2 minutes, follow from there
  docker compose logs --since 2m -f app

  # Follow and grep for a specific request ID (pipe — breaks -f live follow)
  docker compose logs | grep ab12cd34
  # For live-follow + grep: use a subshell
  docker compose logs -f 2>&1 | grep ab12cd34

  # Watch for errors across all services
  docker compose logs -f 2>&1 | grep -i "error\\|exception\\|traceback"

  # Save all logs to a file for post-mortem analysis
  docker compose logs --no-color > debug_$(date +%Y%m%d_%H%M%S).log

Why the color coding matters:
  When following multiple services, each service name gets a distinct color.
  Lines interleave chronologically so you can see the sequence of events
  across services. Combined with request IDs, you can trace:
    app   | request_id=ab12cd34 method=GET path=/items status=200
    db    | LOG:  execute: SELECT id, name...
    redis | SETEX items:all 30 [...]
  These three lines belong to one user request, visible together in sequence.

--- COMMANDS SUMMARY ---

  # Hot-reload dev session
  docker compose up                             # override auto-applied
  # Edit a file → uvicorn restarts in ~1s

  # Run tests (three approaches)
  docker compose exec app python -m pytest tests/ -v                           # exec into running
  docker compose run --rm app python -m pytest tests/ -v                       # fresh + bind mount
  docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app # built image

  # Single test or test class
  docker compose exec app python -m pytest tests/test_api.py::TestItems -v
  docker compose exec app python -m pytest tests/test_api.py::TestItems::test_create_item -v

  # Build with cache visibility
  BUILDKIT_PROGRESS=plain docker compose build  # verbose layer-by-layer output

  # Multi-service log workflows
  docker compose logs -f                        # all services, live
  docker compose logs -f app db                 # specific services
  docker compose logs | grep <request_id>       # trace one request
  docker compose logs -f 2>&1 | grep -i error  # live error watching
"""


TEST_COMMANDS = {
    "exec (running container)":  "docker compose exec app python -m pytest tests/ -v",
    "run (fresh + bind mount)":  "docker compose run --rm app python -m pytest tests/ -v",
    "run (built image, CI-like)": "docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm app",
    "single test class":         "docker compose exec app python -m pytest tests/test_api.py::TestItems -v",
    "single test":               "docker compose exec app python -m pytest tests/test_api.py::TestItems::test_create_item -v",
}

BUILD_CACHE_TYPES = {
    "Layer cache":          "Automatic. COPY+RUN order determines hit rate. Already set up correctly.",
    "BuildKit cache mount": "--mount=type=cache in RUN. Persists pip cache between builds on one machine.",
    "Registry cache (CI)":  "--cache-from/--cache-to with docker buildx. Shares cache across CI runners.",
}

LOG_COMMANDS = {
    "All services, follow":    "docker compose logs -f",
    "One service":             "docker compose logs -f app",
    "Last N lines":            "docker compose logs --tail 50 app",
    "Since N minutes ago":     "docker compose logs --since 5m",
    "Trace request ID":        "docker compose logs | grep <request_id>",
    "Live error watch":        "docker compose logs -f 2>&1 | grep -i error",
    "Save to file":            "docker compose logs --no-color > debug.log",
}


def print_test_commands():
    print("Test commands:")
    for label, cmd in TEST_COMMANDS.items():
        print(f"  [{label}]")
        print(f"    {cmd}")


def print_cache_types():
    print("Build cache mechanisms:")
    for name, desc in BUILD_CACHE_TYPES.items():
        print(f"  {name:<25} {desc}")


def print_log_commands():
    print("Log commands:")
    for label, cmd in LOG_COMMANDS.items():
        print(f"  {label:<25} {cmd}")


if __name__ == "__main__":
    print_test_commands()
    print()
    print_cache_types()
    print()
    print_log_commands()
