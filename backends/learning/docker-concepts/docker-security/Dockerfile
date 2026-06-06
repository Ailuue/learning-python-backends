# syntax=docker/dockerfile:1
# =============================================================================
# Dockerfile — secure implementation
#
# Each fix is labeled [FIX N] corresponding to [ISSUE N] in Dockerfile.insecure.
# Build:  docker compose build
# Check:  docker compose run --rm app /whoami   (or curl the endpoint)
# =============================================================================


# [FIX 1] Pin to a specific version tag. The OS variant (bookworm) is also
# explicit — not relying on the default to stay stable.
#
# For maximum reproducibility, also pin the digest:
#   FROM python:3.12-slim-bookworm@sha256:<digest>
# Get the digest:
#   docker pull python:3.12-slim-bookworm
#   docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim-bookworm
# The digest is immutable — even if the tag moves, your build stays identical.
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt .

# [FIX 2a] Build-time secrets (e.g. private PyPI token) use --mount=type=secret.
# The value is never written to any layer — it's injected only for that RUN step.
# Usage: docker build --secret id=pip_token,src=./secrets/pip_token .
# Then inside the RUN: pip install --extra-index-url $(cat /run/secrets/pip_token) -r requirements.txt
#
# For this public app we don't need a private token, but the cache mount is real:
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt


# =============================================================================
# Runtime stage — only what's needed to run the app
# =============================================================================
# [FIX 3] Minimal base image. python:3.12-slim-bookworm is ~130MB vs ~900MB.
# No compiler, no build tools, no curl, no git. Smaller attack surface.
FROM python:3.12-slim-bookworm

# [FIX 6] Create a non-root user before anything else.
# --system:         service account (no login shell, no crontab, etc.)
# --gid / --uid:    explicit IDs for reproducibility and auditability
# --no-create-home: slightly smaller image; app runs from WORKDIR
#
# Must be done as root (before USER instruction). After USER appuser,
# we can no longer run commands that need root.
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup --no-create-home appuser

# [FIX 2b] Python env vars that prevent unnecessary filesystem writes.
# PYTHONDONTWRITEBYTECODE: no .pyc files → keep the image filesystem clean.
# A read-only filesystem (set in docker-compose.yml) would also block these,
# but setting this prevents errors before the filesystem constraint is applied.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# [FIX 4] Copy only the application code, not secrets/config/git history.
# Combined with .dockerignore, this is a defence-in-depth approach:
#   .dockerignore excludes files from the build context entirely
#   COPY app/ only picks up what the app actually needs at runtime
COPY app/ .

# Set ownership so appuser can read the app files.
# chown must run as root — do it before the USER instruction.
# With read_only: true in compose, appuser can read but not write /app.
RUN chown -R appuser:appgroup /app

# [FIX 6] Switch to non-root user. All subsequent instructions and the
# container process at runtime run as uid 1001, not uid 0.
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
