# Docker Security & Best Practices

Harden Docker images and containers against common vulnerabilities.

## Concepts

1. **Non-root user** — containers run as root by default; add a dedicated user and switch to it
2. **Read-only filesystem** — mount the container's root filesystem as read-only; only allow writes to specific directories via `tmpfs` or named volumes
3. **Secret management** — never bake secrets into images (`ENV`, `ARG`, or `COPY` of `.env`); use Docker secrets or environment variables injected at runtime
4. **Pinned base image versions** — `FROM python:3.12.3-slim` instead of `FROM python:latest` — reproducible builds, no surprise upgrades
5. **Dockerfile security checklist** — minimize layers, avoid `apt-get upgrade`, remove build tools from the final image

## Files

| File / Folder | Purpose |
|---|---|
| `Dockerfile.insecure` | A Dockerfile with common security mistakes |
| `Dockerfile` | Hardened version of the same app |
| `docker-compose.yml` | Shows read-only and secret patterns |
| `secrets/` | Example Docker secrets (never commit real secrets) |
| `app/` | FastAPI app used as the demo target |
| `notes_security.py` | Annotated notes on all concepts |

## Key patterns

```dockerfile
# Pin the base image version
FROM python:3.12.3-slim

# Run as a non-root user
RUN useradd --no-create-home appuser
USER appuser

# Never use ENV or ARG to pass secrets — they appear in image layers
# BAD:  ENV DATABASE_URL=postgres://...
# GOOD: inject at runtime via docker run -e or Docker secrets
```

```yaml
# docker-compose.yml — read-only root filesystem
services:
  app:
    read_only: true
    tmpfs:
      - /tmp          # allow writes only to /tmp
```
