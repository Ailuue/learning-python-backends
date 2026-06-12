# Docker Multi-Stage Builds

Dockerfile fundamentals and the multi-stage build pattern that keeps production images small.

## Concepts

1. **Dockerfile instructions** — `FROM`, `RUN`, `COPY`, `CMD`, `ENTRYPOINT`, `ARG`, `ENV`
2. **Multi-stage builds** — use a heavy builder image to compile/install, then copy only the artifacts into a minimal runtime image
3. **Layer caching** — ordering commands so that rarely-changing layers (e.g. `pip install`) are cached separately from frequently-changing ones (your app code)
4. **Image size comparison** — single-stage vs multi-stage vs Alpine variants

## Files

| File | Description |
|---|---|
| `Dockerfile.single` | Naive single-stage build (large image) |
| `Dockerfile` | Multi-stage build (small runtime image) |
| `Dockerfile.alpine` | Alpine-based variant (even smaller, but glibc trade-offs) |
| `Dockerfile.slim` | Debian slim variant |
| `Dockerfile.buildargs` | Using `ARG` and `ENV` to parameterize builds |
| `notes.py` | Annotated notes on all concepts |
| `notes_optimization.py` | Layer caching tips and size optimization strategies |
| `app/` | Minimal FastAPI app used as the build target |

## Try it

```bash
# Build and compare image sizes
docker build -f Dockerfile.single -t demo:single .
docker build -f Dockerfile -t demo:multi .
docker build -f Dockerfile.alpine -t demo:alpine .
docker images demo
```

## Why multi-stage?

```dockerfile
# Stage 1: builder — has pip, build tools, etc.
FROM python:3.12 AS builder
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# Stage 2: runtime — only the installed packages, not the build tools
FROM python:3.12-slim
COPY --from=builder /install /usr/local
COPY app/ app/
CMD ["uvicorn", "app.main:app"]
```

The final image never contains pip, build headers, or intermediate files.
