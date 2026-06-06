# syntax=docker/dockerfile:1
FROM python:3.12 AS builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY app/requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt


FROM python:3.12-slim AS runtime

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH"

RUN groupadd -g 1001 appgroup && useradd -u 1001 -g appgroup appuser
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv
COPY --chown=appuser:appgroup app/ .

USER appuser

# No EXPOSE — port is intentionally internal only; nginx is the entry point.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
