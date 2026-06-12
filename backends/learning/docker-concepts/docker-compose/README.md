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
| `notes_compose.py` | Annotated notes on all concepts |
| `notes_networking.py` | Container networking deep dive |
| `notes_devworkflow.py` | Local development workflow patterns |
| `app/` | FastAPI app wired to the Postgres service |

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
