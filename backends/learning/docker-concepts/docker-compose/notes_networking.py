"""
Docker Compose — Networking & Communication
============================================

CONCEPTS:
  1. Container networking: how service discovery works under the hood
  2. ports vs expose: controlling what's reachable from where
  3. Health checks: what they test and how Docker uses them
  4. depends_on conditions: the three available conditions
  5. Startup sequencing: what happens without health checks (failure mode)

CHANGES IN THIS SESSION:
  docker-compose.yml  — added healthcheck for the app service

--- THE COMPOSE NETWORK ---

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

--- ports: vs expose: ---

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

--- HEALTH CHECKS ---

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

--- depends_on CONDITIONS ---

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

--- COMMANDS TO RUN ---

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

--- SERVICE DISCOVERY EXERCISES ---

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

--- ports: vs expose: EXERCISE ---

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

--- HEALTH CHECK EXERCISE ---

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

--- WHAT docker compose ps SHOWS ---

Name                     Command               State           Ports
─────────────────────────────────────────────────────────────────────
docker-compose-app-1     uvicorn main:app ...  Up (healthy)    0.0.0.0:8000->8000/tcp
docker-compose-db-1      docker-entrypoint...  Up (healthy)    0.0.0.0:5432->5432/tcp
docker-compose-redis-1   docker-entrypoint...  Up (healthy)    0.0.0.0:6379->6379/tcp

All three should show "Up (healthy)" after a clean start.
If any shows "Up (unhealthy)" or "Up (health: starting)", check:
  docker compose logs <service>
"""


NETWORK_TOPOLOGY = {
    "Within Docker network": {
        "app → db":    "db:5432    (via service name DNS)",
        "app → redis": "redis:6379 (via service name DNS)",
        "db → app":    "app:8000   (any service can reach any other)",
    },
    "From your host machine": {
        "→ app":   "localhost:8000 (ports: mapping)",
        "→ db":    "localhost:5432 (ports: mapping, dev only)",
        "→ redis": "localhost:6379 (ports: mapping, dev only)",
    },
}

HEALTH_CHECK_COMMANDS = {
    "app":   "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health')\"",
    "db":    "pg_isready -U postgres -d appdb",
    "redis": "redis-cli ping",
}

DEPENDS_ON_CONDITIONS = {
    "service_started":              "Container started (NOT ready) — almost always wrong for DBs",
    "service_healthy":              "Health check passed — correct choice for DB and Redis",
    "service_completed_successfully": "Container exited 0 — for migration runners, seed scripts",
}


def print_topology():
    for context, routes in NETWORK_TOPOLOGY.items():
        print(f"{context}:")
        for src, dest in routes.items():
            print(f"  {src:<15} {dest}")
        print()


def print_health_checks():
    print("Health check commands:")
    for service, cmd in HEALTH_CHECK_COMMANDS.items():
        print(f"  {service:<8} {cmd}")


def print_depends_on_conditions():
    print("depends_on conditions:")
    for condition, description in DEPENDS_ON_CONDITIONS.items():
        print(f"  {condition:<38} {description}")


if __name__ == "__main__":
    print_topology()
    print_health_checks()
    print()
    print_depends_on_conditions()
