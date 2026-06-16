# Docker Compose

Multi-service application setup using Docker Compose.

## Concepts

1. **`docker-compose.yml` structure** — `services`, `volumes`, `networks`
2. **Service networking** — the service name is the hostname; containers find each other by name
3. **Named volumes vs bind mounts** — named volumes persist data; bind mounts reflect local file changes in real time (dev workflow)
4. **`depends_on` with health checks** — proper startup ordering so the app waits for Postgres to be ready, not just running
5. **`.env` file** — loaded automatically; use `${VAR}` and `${VAR:-default}` syntax

## Files

| File | Purpose |
|---|---|
| `docker-compose.yml` | Main multi-service definition (app + Postgres) |
| `docker-compose.override.yml` | Dev overrides (bind mounts, hot reload) |
| `docker-compose.test.yml` | Isolated test environment |
| `init.sql` | SQL run on first Postgres startup |
| `app/` | FastAPI app wired to the Postgres service |

Annotated notes — covering Compose basics, container networking, and the local
development workflow — are at the end of this README.

## Try it

```bash
docker compose up -d          # start all services
docker compose logs -f app    # follow app logs
docker compose exec app bash  # shell into the app container
docker compose down -v        # stop and remove volumes
```

## Key pattern — health-check dependency

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy   # waits for the health check to pass

  db:
    image: postgres:16
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      retries: 5
```


---

## Docker Compose — Multi-Service Setup

CONCEPTS:
  1. docker-compose.yml structure: services, volumes, networks
  2. Service-to-service networking: service name IS the hostname
  3. Named volumes vs bind mounts: persistence vs dev workflow
  4. depends_on with health checks: startup ordering done right
  5. .env file: automatic loading, ${VAR} and ${VAR:-default} syntax
  6. docker-compose.override.yml: dev settings merged automatically

SERVICES IN THIS PROJECT:
  app    FastAPI API (built from Dockerfile)       → localhost:8000
  db     PostgreSQL 16                             → localhost:5432
  redis  Redis 7                                   → localhost:6379

FILES:
  docker-compose.yml           base config (production-like)
  docker-compose.override.yml  dev overrides (hot reload, bind mount)
  Dockerfile                   multi-stage build for the app
  app/main.py                  FastAPI with DB + Redis usage
  init.sql                     schema + seed data, runs on first DB startup
  .env                         loaded automatically by Compose (git-ignored)
  .env.example                 safe-to-commit template

### docker-compose.yml STRUCTURE

Top-level keys:
  services:   one entry per container you want to run
  volumes:    named volumes managed by Docker (persistent storage)
  networks:   (optional) custom networks; Compose creates a default one

Each service can define:
  image:        use a pre-built image from a registry
  build:        build an image from a local Dockerfile
  ports:        "host:container" port mapping
  environment:  env vars passed into the container
  volumes:      named volumes OR bind mounts for this service
  depends_on:   startup ordering (with or without health checks)
  healthcheck:  command Compose runs to decide if the service is "healthy"
  restart:      unless-stopped / always / on-failure / no
  command:      override the Dockerfile CMD

### SERVICE NETWORKING

Compose creates a shared network for all services in a project.
Each service is reachable at its SERVICE NAME as the hostname.

  # This connects to the db container at port 5432:
  DATABASE_URL: postgresql://postgres:pass@db:5432/appdb
                                               ^^
                                               service name, not localhost

  # This connects to redis:
  REDIS_URL: redis://redis:6379
                      ^^^^^
                      service name

"localhost" inside a container refers to THAT container, not your host
machine and not other containers. Always use service names.

From your host machine, you reach services through the mapped ports:
  localhost:8000  → app container
  localhost:5432  → db container (exposed for psql/TablePlus)
  localhost:6379  → redis container (exposed for redis-cli)

### NAMED VOLUMES vs BIND MOUNTS

Named volume (postgres_data:/var/lib/postgresql/data):
  - Docker manages the storage in /var/lib/docker/volumes/
  - Persists across container restarts and `docker compose down`
  - Survives `docker compose down` but NOT `docker compose down -v`
  - Best for: databases, any data that must survive a restart

Bind mount (./app:/app):
  - Maps a path on YOUR host to a path in the container
  - Changes on the host are instantly visible in the container
  - Changes in the container write through to the host
  - Best for: dev hot reload — edit code, see it live without rebuilding

### depends_on: THE RIGHT WAY

WRONG — waits for the container to START, not for Postgres to be READY:
  depends_on:
    - db

Postgres takes a few seconds to initialize after starting. Without a
health check condition, your app may connect before Postgres accepts
connections and crash immediately.

RIGHT — waits for the health check to pass:
  depends_on:
    db:
      condition: service_healthy

Combined with a healthcheck in the db service, Compose won't start the
app until pg_isready returns success. No sleep hacks, no retry loops.

### .env FILE

Docker Compose automatically loads .env from the same directory as
docker-compose.yml before processing the file. Variables are substituted
wherever ${VAR} appears.

Syntax:
  ${POSTGRES_PASSWORD}        — must be set or Compose errors
  ${APP_ENV:-production}      — uses "production" if APP_ENV is unset

Rule: never commit .env (add to .gitignore). Commit .env.example instead
as documentation of what variables are required.

The .env file is ONLY for variable substitution in docker-compose.yml.
It is NOT automatically injected into containers — you must explicitly
list variables under `environment:` in the service definition.

### docker-compose.override.yml

Automatically merged on top of docker-compose.yml when you run any
`docker compose` command. No -f flag needed.

Use it to layer dev-only changes:
  - bind mount the source directory for hot reload
  - override CMD to add --reload
  - add debug env vars

To run without the override (simulating production):
  docker compose -f docker-compose.yml up

### COMMANDS

# Start everything (builds if needed, override auto-applied)
docker compose up

# Start in background
docker compose up -d

# View logs (all services)
docker compose logs -f

# View logs for one service
docker compose logs -f app

# Rebuild the app image (e.g. after changing requirements.txt)
docker compose build app
docker compose up -d --no-deps app   # restart only app without touching db/redis

# Stop containers (preserves named volumes)
docker compose down

# Stop and DELETE named volumes (wipes the database!)
docker compose down -v

# List running services and their state
docker compose ps

# Run a command inside a running container
docker compose exec app bash
docker compose exec db psql -U postgres -d appdb
docker compose exec redis redis-cli

# Run a one-off command (starts a temporary container, then exits)
docker compose run --rm app python -c "import fastapi; print(fastapi.__version__)"

# Scale a service (run 3 instances of app)
docker compose up -d --scale app=3

### PRACTICE EXERCISES

1. First run:
     docker compose up
   Watch the startup order — redis and db start first, app waits for their
   health checks to pass before starting.

2. Test the cache:
     curl http://localhost:8000/items          # source: db (first request)
     curl http://localhost:8000/items          # source: cache (subsequent)
     curl -X DELETE http://localhost:8000/items/cache   # bust it
     curl http://localhost:8000/items          # source: db again

3. Add an item and watch cache invalidation:
     curl -X POST http://localhost:8000/items \
       -H 'Content-Type: application/json' \
       -d '{"name": "new item", "description": "added via API"}'
     curl http://localhost:8000/items          # source: db (cache was cleared)
     curl http://localhost:8000/items          # source: cache

4. Verify service networking (from inside the app container):
     docker compose exec app bash
     # curl and redis-cli are not installed in python:3.12-slim.
     # Use Python's socket module instead — always available:
     python3 -c "import socket; print(socket.gethostbyname('db'))"
     python3 -c "import socket; print(socket.gethostbyname('redis'))"
     python3 -c "import socket; socket.create_connection(('db', 5432), timeout=2); print('db reachable')"
     python3 -c "import socket; socket.create_connection(('redis', 6379), timeout=2); print('redis reachable')"

5. Hot reload demo (override is already active):
     # Edit app/main.py — change the root() message
     # Save the file — watch the docker compose logs -f app output
     # uvicorn detects the change and restarts automatically
     curl http://localhost:8000   # see your change without rebuilding

6. Persistence demo:
     curl -X POST http://localhost:8000/items \
       -H 'Content-Type: application/json' \
       -d '{"name": "persistent item"}'
     docker compose down          # stop containers
     docker compose up -d         # restart
     curl http://localhost:8000/items   # your item is still there (named volume)

     docker compose down -v       # now delete volumes
     docker compose up -d
     curl http://localhost:8000/items   # back to seed data only (init.sql ran again)

7. Connect to Postgres directly from your host:
     docker compose exec db psql -U postgres -d appdb   # always reliable

     # Alternatively from the host:
     psql -h localhost -U postgres -d appdb
     # GOTCHA: if you have PostgreSQL installed via Homebrew and it's running,
     # psql -h localhost hits THAT instead of the Docker container — it won't
     # have appdb. Check with: brew services list | grep postgresql
     # Fix: brew services stop postgresql@<version>  (while practicing)

8. Connect to Redis from your host:
     docker compose exec redis redis-cli   # always reliable
     KEYS *
     TTL items:all

     # Alternatively from the host:
     redis-cli -p 6379
     # GOTCHA: same issue as Postgres — if Homebrew Redis is running, redis-cli
     # hits that instance (which is empty) instead of the Docker container.
     # Check: brew services list | grep redis
     # Fix: brew services stop redis  (while practicing)


---

## Development Workflow

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

### HOT-RELOAD

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

### RUNNING TESTS INSIDE CONTAINERS

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

### DOCKER BUILD CACHE

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

    RUN --mount=type=cache,target=/root/.cache/pip         pip install -r requirements.txt

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
  docker buildx build     --cache-to type=registry,ref=ghcr.io/user/myapp:cache,mode=max     --cache-from type=registry,ref=ghcr.io/user/myapp:cache     -t myapp:latest .

  The CI runner pulls the cache from the registry, uses it for the build,
  then pushes the updated cache back. Next CI run pulls the fresh cache.
  mode=max caches ALL layers; mode=min (default) only the final stage.

Watch the cache in action:
  docker compose build        # first build — all layers fresh
  # (change a line in app/main.py)
  docker compose build        # second build — pip install should be CACHED
  # Output: => CACHED [builder 5/5] RUN --mount=type=cache...  0.0s

### REQUEST TRACING

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

### docker compose logs — MULTI-SERVICE

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
  docker compose logs -f 2>&1 | grep -i "error\|exception\|traceback"

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

### COMMANDS SUMMARY

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


---

## Docker Compose — Networking & Communication

CONCEPTS:
  1. Container networking: how service discovery works under the hood
  2. ports vs expose: controlling what's reachable from where
  3. Health checks: what they test and how Docker uses them
  4. depends_on conditions: the three available conditions
  5. Startup sequencing: what happens without health checks (failure mode)

CHANGES IN THIS SESSION:
  docker-compose.yml  — added healthcheck for the app service

### THE COMPOSE NETWORK

When you run `docker compose up`, Docker automatically creates a network
named <project>_default (usually the folder name + _default). Every service
is attached to this network. No configuration required.

Within this network, each service is registered under its service name as a
DNS hostname. Docker runs an internal DNS server that resolves these names:

  Inside any container:
    "db"    → resolves to the db container's IP address
    "redis" → resolves to the redis container's IP address
    "app"   → resolves to the app container's IP address

  From your host machine:
    "db", "redis", "app" do NOT resolve (not on your host's DNS)
    You reach them only through mapped ports: localhost:5432, localhost:6379

This is why DATABASE_URL uses "db:5432" and not "localhost:5432". Inside the
app container, "localhost" is the app container itself — not the db container.

The shared network also means every service can reach every other service
on any port, regardless of whether that port is listed under ports: or expose:.
The network access is open within the project. ports: and expose: only
control what's reachable from OUTSIDE the Docker network (your host machine).

### ports: vs expose:

  ports:
    - "5432:5432"       host_port:container_port

    Reachable from:
      ✓ Other services on the Docker network (at db:5432)
      ✓ Your host machine (at localhost:5432)
      ✓ Anything that can reach your host machine (public if no firewall)

  expose:
    - "5432"

    Reachable from:
      ✓ Other services on the Docker network (at db:5432)
      ✗ Your host machine (localhost:5432 → connection refused)

  Neither ports: nor expose: listed:

    Reachable from:
      ✓ Other services on the Docker network (still works — the network
        is open between services regardless)
      ✗ Your host machine

Practical rule:
  Only use ports: for services that genuinely need to be reachable from
  outside Docker. In production that is usually just your API (app).
  Database and cache services should have no ports: mapping.

This project uses ports: on all three services for dev convenience
(connect from TablePlus, redis-cli, psql on your host). In a real
deployment you'd drop ports: from db and redis entirely.

Note: expose: is largely informational in Compose V2. The actual
networking behavior is determined by the shared default network, not
by the expose: declaration. It serves as documentation of which ports
a service uses.

### HEALTH CHECKS

A healthcheck tells Docker how to test whether a service is actually
ready to handle work — not just whether the process started.

Structure:
  healthcheck:
    test: the command to run
    interval: how often to run it (default 30s)
    timeout: max time to wait for the command (default 30s)
    retries: failures before marking unhealthy (default 3)
    start_period: grace window before failures count (default 0s)

test command forms:
  ["CMD", "executable", "arg1", ...]
    Runs the executable directly. No shell. Arguments passed as-is.
    Use when you don't need shell features (pipes, redirects, globs).

  ["CMD-SHELL", "shell command string"]
    Runs through /bin/sh -c. Needed for shell operators: &&, ||, pipes.
    Quoting becomes your problem — be careful.

  ["NONE"]
    Disables a health check inherited from the base image.

Health states a container can be in:
  starting   — within start_period, failures don't count yet
  healthy    — last N checks passed
  unhealthy  — failed retries consecutive times

The health checks in this project:

  db:
    pg_isready -U postgres -d appdb
    Built-in Postgres tool. Returns 0 when Postgres is accepting connections.
    Nothing to install — it's in every postgres image.

  redis:
    redis-cli ping
    Returns "PONG" (exit 0) when Redis is responsive.
    Built-in to every redis image.

  app:
    python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
    Calls our /health endpoint. urlopen raises an exception (exit non-zero)
    on connection failure or HTTP error. Exits 0 on success.
    Uses Python's stdlib — no extra tools needed in the slim image.
    start_period: 15s gives uvicorn time to start before checks begin.

start_period is important for the app: Docker sends health checks immediately
after the container starts. Without start_period, early failures (while
uvicorn is still booting) would burn through retries and mark the service
unhealthy before it even had a chance to become ready.

### depends_on CONDITIONS

depends_on controls startup ordering. Three conditions are available:

  condition: service_started     (default when you just list a service name)
    Wait for the container to START. Does not wait for it to be ready.
    Postgres starts almost instantly but takes seconds to be usable.
    This condition is almost always the wrong choice for databases.

  condition: service_healthy
    Wait for the health check to report healthy.
    Requires the dependency service to have a healthcheck: defined.
    This is the correct choice for DB and Redis.

  condition: service_completed_successfully
    Wait for the container to EXIT with code 0.
    Used for one-off setup tasks: database migrations, seed scripts,
    test runners — services that are expected to finish and exit.

Without depends_on (or with just service_started):
  1. app container starts
  2. uvicorn starts, app code runs
  3. psycopg2.connect("postgresql://...@db:5432/appdb") is called
  4. Postgres hasn't finished initializing yet
  5. Connection refused / "FATAL: database does not exist"
  6. app crashes immediately

With condition: service_healthy:
  1. db container starts
  2. pg_isready runs every 5s
  3. Postgres finishes initializing
  4. pg_isready returns success — db is now "healthy"
  5. app container starts (only now)
  6. psycopg2.connect succeeds immediately

### COMMANDS TO RUN

# Start everything and watch the startup sequence
docker compose up

# Start detached, then follow logs to watch health checks
docker compose up -d
docker compose logs -f

# Check the current health status of every service
docker compose ps

# Watch health checks in real time (one service)
watch docker compose ps

# See detailed container info including health check history
docker inspect docker-compose-app-1 | python3 -m json.tool | grep -A 20 Health

# Get just the health status
docker inspect --format='{{.State.Health.Status}}' docker-compose-db-1

### SERVICE DISCOVERY EXERCISES

# 1. Confirm DNS resolution from inside the app container
docker compose exec app bash
  # Inside the container:
  cat /etc/resolv.conf            # Docker's internal DNS server (127.0.0.11)
  python3 -c "import socket; print(socket.gethostbyname('db'))"
  python3 -c "import socket; print(socket.gethostbyname('redis'))"
  python3 -c "import socket; print(socket.gethostbyname('app'))"
  # All three resolve to IP addresses on the 172.x.x.x range

# 2. Verify the connection URLs work from inside the container
docker compose exec app python3 -c "
import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'])
print('DB connected:', conn.status)
conn.close()
"

docker compose exec app python3 -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('Redis ping:', r.ping())
"

# 3. Confirm localhost means THIS container, not others
docker compose exec app python3 -c "
import socket
print(socket.gethostbyname('localhost'))   # 127.0.0.1 — the app container itself
"

### ports: vs expose: EXERCISE

# Currently, db is mapped to localhost:5432 via ports:
# This works from your host terminal:
psql -h localhost -U postgres -d appdb   # connects fine

# To see what happens without ports:, comment out the ports block in
# docker-compose.yml for the db service and restart:
#   db:
#     # ports:        ← comment this out
#     #   - "5432:5432"
# docker compose up -d --no-deps --build db
# psql -h localhost -U postgres -d appdb   # connection refused from host

# But from inside the app container, db is still reachable:
# docker compose exec app python3 -c "import psycopg2, os; psycopg2.connect(os.environ['DATABASE_URL']); print('still works')"

### HEALTH CHECK EXERCISE

# Watch a service go from starting → healthy
docker compose up -d
watch -n 1 "docker compose ps"
# The STATUS column shows: starting → healthy (or unhealthy if something is wrong)

# Simulate the failure mode: start app without waiting for db to be healthy
# (for understanding only — don't do this in real configs)
# Temporarily change depends_on in docker-compose.yml to:
#   depends_on:
#     db:
#       condition: service_started
# Then: docker compose down -v && docker compose up
# Watch the app fail immediately because DB isn't ready yet

### WHAT docker compose ps SHOWS

Name                     Command               State           Ports
─────────────────────────────────────────────────────────────────────
docker-compose-app-1     uvicorn main:app ...  Up (healthy)    0.0.0.0:8000->8000/tcp
docker-compose-db-1      docker-entrypoint...  Up (healthy)    0.0.0.0:5432->5432/tcp
docker-compose-redis-1   docker-entrypoint...  Up (healthy)    0.0.0.0:6379->6379/tcp

All three should show "Up (healthy)" after a clean start.
If any shows "Up (unhealthy)" or "Up (health: starting)", check:
  docker compose logs <service>
