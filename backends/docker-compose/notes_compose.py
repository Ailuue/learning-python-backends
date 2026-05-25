"""
Docker Compose — Multi-Service Setup
======================================

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

--- docker-compose.yml STRUCTURE ---

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

--- SERVICE NETWORKING ---

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

--- NAMED VOLUMES vs BIND MOUNTS ---

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

--- depends_on: THE RIGHT WAY ---

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

--- .env FILE ---

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

--- docker-compose.override.yml ---

Automatically merged on top of docker-compose.yml when you run any
`docker compose` command. No -f flag needed.

Use it to layer dev-only changes:
  - bind mount the source directory for hot reload
  - override CMD to add --reload
  - add debug env vars

To run without the override (simulating production):
  docker compose -f docker-compose.yml up

--- COMMANDS ---

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

--- PRACTICE EXERCISES ---

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
     curl -X POST http://localhost:8000/items \\
       -H 'Content-Type: application/json' \\
       -d '{"name": "new item", "description": "added via API"}'
     curl http://localhost:8000/items          # source: db (cache was cleared)
     curl http://localhost:8000/items          # source: cache

4. Verify service networking (from inside the app container):
     docker compose exec app bash
     # These work because service names resolve on the compose network:
     curl db:5432       # will fail (not HTTP) but DNS resolves
     redis-cli -h redis ping   # may not be installed, but try

5. Hot reload demo (override is already active):
     # Edit app/main.py — change the root() message
     # Save the file — watch the docker compose logs -f app output
     # uvicorn detects the change and restarts automatically
     curl http://localhost:8000   # see your change without rebuilding

6. Persistence demo:
     curl -X POST http://localhost:8000/items \\
       -H 'Content-Type: application/json' \\
       -d '{"name": "persistent item"}'
     docker compose down          # stop containers
     docker compose up -d         # restart
     curl http://localhost:8000/items   # your item is still there (named volume)

     docker compose down -v       # now delete volumes
     docker compose up -d
     curl http://localhost:8000/items   # back to seed data only (init.sql ran again)

7. Connect to Postgres directly from your host:
     psql -h localhost -U postgres -d appdb
     # password is in .env: POSTGRES_PASSWORD=localpass

8. Connect to Redis from your host:
     redis-cli -p 6379
     KEYS *               # see what's cached
     TTL items:all        # see how many seconds until cache expires
"""


SERVICES = {
    "app":   "FastAPI API — localhost:8000",
    "db":    "PostgreSQL 16 — localhost:5432 (also reachable as 'db' inside containers)",
    "redis": "Redis 7 — localhost:6379 (also reachable as 'redis' inside containers)",
}

QUICK_COMMANDS = {
    "Start all":          "docker compose up",
    "Start (background)": "docker compose up -d",
    "View logs":          "docker compose logs -f",
    "Rebuild app":        "docker compose build app && docker compose up -d app",
    "Stop (keep data)":   "docker compose down",
    "Stop (wipe data)":   "docker compose down -v",
    "Shell in app":       "docker compose exec app bash",
    "psql":               "docker compose exec db psql -U postgres -d appdb",
    "redis-cli":          "docker compose exec redis redis-cli",
}


def print_services():
    print("Services:")
    for name, desc in SERVICES.items():
        print(f"  {name:<8} {desc}")


def print_commands():
    print("Quick commands:")
    for label, cmd in QUICK_COMMANDS.items():
        print(f"  {label:<22} {cmd}")


if __name__ == "__main__":
    print_services()
    print()
    print_commands()
