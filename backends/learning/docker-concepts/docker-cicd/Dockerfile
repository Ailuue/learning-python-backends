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

# BUILD_SHA is passed in from CI via --build-arg BUILD_SHA=${{ github.sha }}.
# It is baked into the image as an ENV var so /version can read it at runtime.
# Placed late in the Dockerfile so that changing the SHA doesn't bust the
# pip layer cache — only the final COPY and this ARG/ENV change per commit.
ARG BUILD_SHA=local-build
ENV BUILD_SHA=$BUILD_SHA

RUN groupadd -g 1001 appgroup && useradd -u 1001 -g appgroup appuser
COPY --from=builder --chown=appuser:appgroup /opt/venv /opt/venv
COPY --chown=appuser:appgroup app/ .

USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
