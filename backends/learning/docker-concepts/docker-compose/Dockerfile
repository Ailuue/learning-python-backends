# syntax=docker/dockerfile:1
# The directive above (must be line 1) enables BuildKit advanced features,
# including --mount=type=cache used below.

# Multi-stage — same pattern as docker-multi-stage/Dockerfile.
# Builder installs deps into a venv; runtime copies only the venv.

FROM python:3.12 AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt .

# --mount=type=cache persists pip's download cache in a BuildKit cache volume.
# The cache lives outside the image layer — it doesn't bloat the final image.
# On subsequent builds, pip reads from this cache instead of re-downloading,
# which cuts install time dramatically for large dependency sets.
# Note: --no-cache-dir is removed so pip can use the cache mount.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt


FROM python:3.12-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY app/ .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
