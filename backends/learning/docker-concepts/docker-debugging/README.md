# Container Debugging & Inspection

Tools and techniques for understanding what's happening inside a running container.

## Concepts

1. **`docker exec`** — run a command or open a shell inside a running container
2. **`docker logs`** — tail, follow, timestamp, and time-range filter container output
3. **`docker inspect`** — dump the full container config: networking, mounts, env vars, health check history
4. **Fixing a broken container** — the `broken/` subfolder has a deliberately misconfigured app with three bugs to diagnose and fix
5. **Resource limits** — set memory and CPU caps; observe what happens when a container exceeds them

## Files

| File / Folder | Purpose |
|---|---|
| `broken/` | A broken FastAPI container — find and fix three issues |

An annotated reference for all the debugging commands is at the end of this README.

## Essential commands

```bash
# Open an interactive shell
docker exec -it <container> bash

# Follow logs with timestamps
docker logs -f --timestamps <container>

# Show only the last 50 lines
docker logs --tail 50 <container>

# Inspect everything about a container
docker inspect <container>

# Filter inspect output with Go templates
docker inspect -f '{{.NetworkSettings.Networks}}' <container>
docker inspect -f '{{.State.Health.Log}}' <container>   # health check history

# Resource limits
docker run --memory="256m" --cpus="0.5" my-image
```

## Broken container exercise

```bash
cd broken
docker compose up --build
# The app fails to start — read the logs and fix the three issues
```

Hints are in the debugging notes at the end of this README.


---

## Container Debugging & Inspection

CONCEPTS:
  1. docker exec: shell into and run commands in running containers
  2. docker logs: follow, tail, timestamps, time-range filtering
  3. docker inspect: examine config, networking, mounts, health history
  4. Debug a deliberately broken container — fix 3 issues
  5. Resource limits: memory and CPU constraints

THE BROKEN STACK:  broken/
  broken/Dockerfile          Bug 1: wrong port in CMD
  broken/docker-compose.yml  Bug 2: wrong db hostname
                             Bug 3: wrong init.sql mount path
  broken/app/main.py         simple FastAPI + psycopg2 app
  broken/.env                db credentials

### docker exec

Runs a command inside an already-running container.
The container must be in the "running" state — exec does not start stopped containers.

  docker exec [OPTIONS] CONTAINER COMMAND [ARGS...]

Common forms:

  # Open an interactive shell (bash)
  docker exec -it mycontainer bash

  # Open sh (use when bash is not installed — alpine images)
  docker exec -it mycontainer sh

  # Run a single non-interactive command
  docker exec mycontainer env
  docker exec mycontainer cat /etc/os-release

  # Run as a specific user (useful when the container runs as non-root)
  docker exec -it --user root mycontainer bash

  # Set environment variables for the exec session
  docker exec -e DEBUG=1 mycontainer python manage.py shell

  # Exec in a Compose service (Compose resolves the container name for you)
  docker compose exec app bash
  docker compose exec db psql -U postgres -d debugdb
  docker compose exec redis redis-cli

Flags:
  -i   Keep stdin open (needed for interactive input)
  -t   Allocate a pseudo-TTY (needed for a proper terminal)
  -it  Always use together for interactive shells
  -e   Set an environment variable in the exec session
  -u   Run as this user
  -w   Set the working directory

Things to do once inside a container:
  env                         all environment variables
  cat /etc/hosts              how DNS is configured
  cat /etc/resolv.conf        Docker's internal DNS server (127.0.0.11)
  ls -la /app                 verify files were COPYed correctly
  pip list                    confirm installed packages
  python -c "import pkg"      test an import
  ps aux                      running processes
  netstat -tlnp               listening ports (if net-tools installed)
  curl localhost:8000/health  test the app from inside its own container

### docker logs

Fetches logs from a container's stdout and stderr.

  docker logs [OPTIONS] CONTAINER

  # Follow logs in real time (Ctrl+C to stop)
  docker logs -f mycontainer
  docker compose logs -f app

  # Last N lines only
  docker logs --tail 50 mycontainer
  docker logs --tail 0 -f mycontainer   # follow from now, no history

  # With timestamps (Docker adds these, separate from your app's own timestamps)
  docker logs -t mycontainer
  docker logs -tf mycontainer           # follow + timestamps

  # From a relative time ago
  docker logs --since 5m mycontainer    # last 5 minutes
  docker logs --since 1h mycontainer    # last hour
  docker logs --since 30s mycontainer   # last 30 seconds

  # Absolute timestamp (RFC 3339 or Unix)
  docker logs --since 2024-01-15T09:00:00 mycontainer

  # Up to a point in time
  docker logs --until 5m mycontainer

  # Combine: last 10 minutes, follow from there
  docker logs --since 10m -f mycontainer

  # Multiple services with Compose
  docker compose logs -f app db redis
  docker compose logs --tail 20 app

What to look for:
  Container exited immediately  → look for Python tracebacks, ImportError,
                                  connection refused, env var KeyError
  App running but wrong port    → "Uvicorn running on http://0.0.0.0:XXXX"
  DB connection failure         → "could not translate host name"
                                  "Connection refused"
                                  "password authentication failed"
  Startup order issues          → connection errors right at startup
                                  (before depends_on health check kicks in)

### docker inspect

Returns detailed JSON about a container (or image, network, volume).
The raw output is verbose — use --format to extract specific fields.

  docker inspect CONTAINER          # full JSON output
  docker inspect IMAGE              # works on images too
  docker network inspect NETWORK
  docker volume inspect VOLUME

Useful --format patterns:

  # Container state (running, exited, etc.) and exit code
  docker inspect --format='{{.State.Status}} (exit {{.State.ExitCode}})' mycontainer

  # Error message if the container exited with a non-zero code
  docker inspect --format='{{.State.Error}}' mycontainer

  # All environment variables, one per line
  docker inspect --format='{{range .Config.Env}}{{println .}}{{end}}' mycontainer

  # Port bindings (what host ports map to container ports)
  docker inspect --format='{{json .NetworkSettings.Ports}}' mycontainer | python3 -m json.tool

  # IP address on the default bridge network
  docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' mycontainer

  # Volume mounts (source on host → destination in container)
  docker inspect --format='{{range .Mounts}}{{.Source}} → {{.Destination}}{{println}}{{end}}' mycontainer

  # Health check current status
  docker inspect --format='{{.State.Health.Status}}' mycontainer

  # Full health check history (last 5 results)
  docker inspect --format='{{json .State.Health}}' mycontainer | python3 -m json.tool

  # Image the container was built from
  docker inspect --format='{{.Config.Image}}' mycontainer

  # When the container was started
  docker inspect --format='{{.State.StartedAt}}' mycontainer

  # Restart policy
  docker inspect --format='{{.HostConfig.RestartPolicy.Name}}' mycontainer

Tip: for ad-hoc exploration, pipe the raw JSON to python3 -m json.tool
and search with grep:
  docker inspect mycontainer | python3 -m json.tool | grep -A 5 '"Mounts"'

### THE DEBUGGING EXERCISE

The broken/ directory has 3 deliberate bugs. Work through them in order.
Each bug requires a different tool to diagnose.

Run from inside the broken/ directory:
  cd broken/
  docker compose up

─────────────────────────────────────────────────────────────────────
BUG 1 — Symptom: curl localhost:8000 → connection refused
         even though docker compose ps shows the app container as "Up"
─────────────────────────────────────────────────────────────────────

The container is running but nothing is answering on port 8000.

Diagnose with docker logs:
  docker compose logs app
  # Look for: "Uvicorn running on http://0.0.0.0:XXXX"
  # XXXX is not 8000 — that's the bug.

What you'll see:
  INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)

The compose file maps 8000 (host) → 8000 (container). But uvicorn is
listening on 9000 inside the container. Port 8000 in the container is
empty — nothing receives the forwarded requests.

Fix: in broken/Dockerfile, change the CMD port from 9000 to 8000.
Then rebuild: docker compose build app && docker compose up -d app

─────────────────────────────────────────────────────────────────────
BUG 2 — Symptom: app container starts then exits immediately
         (STATUS shows "Exited" in docker compose ps)
─────────────────────────────────────────────────────────────────────

After fixing Bug 1, the app starts but crashes on startup.

Diagnose with docker logs:
  docker compose logs app
  # Look for: "could not translate host name "database""
  # or: OperationalError / connection refused

The error names a host that doesn't exist on the Docker network.

Confirm with docker exec (if the container is still briefly running) or
check the env var directly in the compose config:
  docker compose exec app env | grep DATABASE_URL
  # or, since it crashes too fast, inspect the container config:
  docker inspect docker-debugging-broken-app-1 --format \
    '{{range .Config.Env}}{{println .}}{{end}}' | grep DATABASE

What you'll see:
  DATABASE_URL=postgresql://postgres:debugpass@database:5432/debugdb
                                               ^^^^^^^^
                                               no service named "database"

Fix: in broken/docker-compose.yml, change "database" to "db" in DATABASE_URL.
No rebuild needed (it's an env var change): docker compose up -d app

─────────────────────────────────────────────────────────────────────
BUG 3 — Symptom: all three services are "Up (healthy)", app responds,
         but GET /items returns an error: "relation 'items' does not exist"
─────────────────────────────────────────────────────────────────────

After fixing Bug 2, the stack is fully up and the app connects to the DB.
But when you hit GET /items, psycopg2 throws an error — the table doesn't exist.

Step 1 — check whether init.sql ran:
  docker compose exec db ls /docker-entrypoint-initdb.d/
  # Expected: init.sql
  # Actual:   (empty directory)

Step 2 — confirm where init.sql was actually mounted:
  docker inspect docker-debugging-broken-db-1 --format \
    '{{range .Mounts}}{{.Source}} → {{.Destination}}{{println}}{{end}}'
  # You'll see: .../init.sql → /tmp/init.sql
  # It was mounted to /tmp, not to /docker-entrypoint-initdb.d/

The postgres image only runs *.sql files placed in /docker-entrypoint-initdb.d/
on first startup (when the data volume is empty). init.sql landed in /tmp
and was silently ignored.

Fix (two steps):
  1. In broken/docker-compose.yml, change the volume mount destination:
       - ./init.sql:/tmp/init.sql           ← wrong
       + ./init.sql:/docker-entrypoint-initdb.d/init.sql   ← correct
  2. Delete the existing postgres volume and restart so init.sql runs again:
       docker compose down -v   ← -v deletes named volumes
       docker compose up

Verify the fix:
  curl http://localhost:8000/items
  # Should return: [{"id":1,"name":"alpha"},{"id":2,"name":"beta"},...]

─────────────────────────────────────────────────────────────────────
SOLVED — what each bug taught:
  Bug 1: docker logs  → read what the process actually did (port mismatch)
  Bug 2: docker logs + docker inspect  → env var typo in a running container
  Bug 3: docker exec + docker inspect  → volume mount path misconfiguration
─────────────────────────────────────────────────────────────────────

### RESOURCE LIMITS

Without limits, a single container can consume all available memory and CPU
on the host, starving other containers or the host OS itself.

In docker-compose.yml, add limits under deploy.resources:

  services:
    app:
      deploy:
        resources:
          limits:
            memory: 256M    # container is OOM-killed if it exceeds this
            cpus: "0.5"     # max 50% of one CPU core
          reservations:
            memory: 64M     # Docker guarantees this minimum is available
            cpus: "0.1"     # Docker reserves this share for this container

Memory units: b, k, m, g  (128M, 1G, 512k, etc.)
CPU value: a float, "1.0" = one full core, "0.5" = half a core, "2.0" = two cores

What happens when limits are hit:
  Memory limit exceeded  → container receives SIGKILL (OOM kill)
                           docker logs shows "Killed"
                           docker inspect shows OOMKilled: true
  CPU limit exceeded     → container is throttled (slowed down, not killed)

Check if a container was OOM-killed:
  docker inspect --format='{{.State.OOMKilled}}' mycontainer   # true/false

Practical guidance:
  Always set limits in production — a memory leak in one service should
  not take down the entire host.
  Start permissive, then tighten: watch actual usage with `docker stats`,
  then set limits at ~2x the normal peak.

Monitor live resource usage:
  docker stats                      # all containers, live
  docker stats mycontainer          # one container
  docker stats --no-stream          # snapshot, not live (good for scripts)

  Output columns:
  NAME         CPU%    MEM USAGE / LIMIT    MEM%    NET I/O    BLOCK I/O
  app          0.5%    45MB / 256MB         17.6%   ...        ...

### QUICK REFERENCE

Workflow for a broken container:

  1. docker compose ps
     → Is the container running? Exited? What's the status?

  2. docker compose logs <service>
     → What did the process print before dying?
     → What port is it listening on?
     → Any Python tracebacks?

  3. docker compose exec <service> bash (or sh)
     → Can I get inside? (Only works if container is running)
     → Check env vars, files, network resolution

  4. docker inspect <container>
     → Correct env vars? Correct port bindings? Correct volume mounts?
     → What's the health check showing?
     → OOMKilled?

  5. docker stats
     → Is the container hitting memory or CPU limits?
