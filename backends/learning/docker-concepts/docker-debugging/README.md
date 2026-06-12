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
| `notes_debugging.py` | Annotated reference for all debugging commands |
| `broken/` | A broken FastAPI container — find and fix three issues |

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

Hints are in `notes_debugging.py`.
