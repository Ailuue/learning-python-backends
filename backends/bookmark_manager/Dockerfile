# ── Stage 1: install dependencies into an isolated virtualenv ─────────────────
FROM python:3.13-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN python -m venv /venv && \
    /venv/bin/pip install --no-cache-dir -r requirements.txt


# ── Stage 2: lean runtime image ───────────────────────────────────────────────
FROM python:3.13-slim AS runtime
WORKDIR /app

# Copy only the pre-built virtualenv — no pip or build tools in the final image
COPY --from=builder /venv /venv

# Copy application code and Alembic migrations
COPY . .

# Run as a non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

ENV PATH="/venv/bin:$PATH"
EXPOSE 8000

# Default command — overridden for worker/beat in docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
