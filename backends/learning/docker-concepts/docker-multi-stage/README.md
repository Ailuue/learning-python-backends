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
| `app/` | Minimal FastAPI app used as the build target |

Annotated notes on all the concepts — plus layer-caching and size-optimization
tips — are at the end of this README.

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


---

## Docker Multi-Stage Builds

CONCEPTS:
  1. Dockerfile basics: FROM, RUN, COPY, CMD, ENTRYPOINT
  2. Multi-stage builds: separate builder vs runtime image
  3. Layer caching: order commands for cache hits
  4. Image size comparison: single-stage vs multi-stage

FILES:
  app/main.py          — the FastAPI app being containerized
  app/requirements.txt — pinned dependencies
  .dockerignore        — excludes files from the build context
  Dockerfile.single    — single-stage (large, simple)
  Dockerfile           — multi-stage (small, production-ready)

### DOCKERFILE BASICS

FROM <image>:<tag>
  The base image. Every Dockerfile starts from one.
  python:3.12        ~900MB — full Python install, build tools included
  python:3.12-slim   ~130MB — stripped down, enough to run Python apps
  python:3.12-alpine  ~50MB — even smaller, uses musl libc (can cause
                              C-extension compatibility issues — avoid for
                              heavy deps like numpy, psycopg2)

RUN <command>
  Executes a shell command during the build. Each RUN creates a new image
  layer. Combine related commands with && to keep layers small:
    RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY <src> <dest>
  Copies files from the build context (your local machine) into the image.
  The build context is the directory you pass to `docker build` (usually `.`).
  .dockerignore controls what's excluded from the context.

CMD ["executable", "arg"]
  Default command when the container starts. Overrideable at runtime:
    docker run myimage bash    ← CMD is replaced entirely

ENTRYPOINT ["executable"]
  Fixes the executable. Runtime args are appended, not replaced:
    docker run myimage --reload    ← appended to ENTRYPOINT
  Use CMD for flexibility, ENTRYPOINT when the image has exactly one purpose.

### LAYER CACHING

Docker caches each layer keyed on its inputs. If the inputs haven't changed
since the last build, Docker reuses the cached layer — no recomputation.

Invalidation is cascading: if layer N changes, all layers after N are
rebuilt, even if their inputs are identical.

WRONG order — busts the cache on every code change:
  COPY app/ .                          ← any code change invalidates this
  RUN pip install -r requirements.txt  ← re-runs even if deps are unchanged

RIGHT order — deps cached independently from code:
  COPY app/requirements.txt .          ← only changes when deps change
  RUN pip install -r requirements.txt  ← cached until requirements change
  COPY app/ .                          ← code changes don't re-run pip

Rule: put things that change RARELY early; things that change OFTEN late.

### MULTI-STAGE STRATEGY

The core problem: build tools (pip, compilers, gcc) are needed at build time
but are dead weight at runtime. A running uvicorn process doesn't need pip.

Stage 1 — builder:
  Start from the full image. Install everything. The mess stays here.

Stage 2 — runtime:
  Start from a slim image. Use COPY --from=builder to pull over ONLY the
  installed packages (the venv directory). Nothing else follows.

  COPY --from=builder /opt/venv /opt/venv

The final image is clean: no pip, no build cache, no compiler. Just Python
and your installed packages.

### PRACTICE COMMANDS

# 1. Build both images
docker build -f Dockerfile.single -t fastapi-single .
docker build -t fastapi-multi .

# 2. Compare sizes — this is the payoff
docker images | grep fastapi

# 3. Run the multi-stage image
docker run -p 8000:8000 fastapi-multi

# 4. Test it (in another terminal)
curl http://localhost:8000
curl http://localhost:8000/health
curl "http://localhost:8000/items/42?q=docker"

# 5. See the layers in each image — notice how many fewer layers fastapi-multi has
docker history fastapi-single
docker history fastapi-multi

# 6. Explore inside the running container
docker run -it --entrypoint bash fastapi-multi
  # Inside: ls, python --version, pip list
  # Try: which pip   → /opt/venv/bin/pip
  # pip IS present — it's part of the venv and copied with it.
  # The compiler (gcc, g++) is what's absent, not pip itself.

# 7. Layer cache demo — experience the caching speedup
#    Edit app/main.py (change the "message" string in root())
#    Then rebuild:
docker build -t fastapi-multi .
#    Watch for "CACHED" on the pip install step — deps didn't change,
#    so Docker skips that layer entirely. Only the COPY app/ layer reruns.

# 8. CMD override at runtime
docker run fastapi-multi uvicorn main:app --host 0.0.0.0 --port 8000 --reload
#    The CMD is replaced entirely. The image still works, just with --reload.

### THINGS TO NOTICE

- fastapi-single is ~1GB, fastapi-multi is ~200MB (roughly 5x smaller)
- `docker history` shows fastapi-multi has far fewer layers
- pip IS present in the runtime image — `python -m venv` installs it into the
  venv by default, and COPY --from=builder copies the whole venv including pip.
  The size saving comes from the slim base image, not from removing pip.
  To truly strip pip: `pip uninstall pip setuptools wheel -y` at the end of
  the builder stage, before COPY --from=builder runs.
- Rebuilding after a code change reuses the pip install layer (CACHED)
- The .dockerignore keeps __pycache__ and other non-build files out of the
  build context, keeping things clean and preventing accidental cache busts


---

## Image Optimization

CONCEPTS:
  1. Base image selection: alpine vs slim vs full
  2. Reduce image size: combine RUN layers, remove caches
  3. .dockerignore: exclude venv, __pycache__, .git
  4. ARG vs ENV: build-time vs runtime variables

NEW FILES THIS SESSION:
  Dockerfile.slim       — single-stage, slim base (~250MB)
  Dockerfile.alpine     — alpine multi-stage (~100MB, caveats)
  Dockerfile.buildargs  — ARG and ENV comprehensive demo
  app/requirements.alpine.txt — no C-extension deps (for alpine compat)

### BASE IMAGE SELECTION

Base images come in three tiers for most languages:

  Tag             Approx Size   Base OS          Notes
  ─────────────── ───────────── ──────────────── ─────────────────────────────
  python:3.12     ~900MB        Debian (full)    Everything installed; build
                                                 tools, pip, gcc — safe but fat
  python:3.12-slim ~130MB       Debian (minimal) Just Python runtime; no build
                                                 tools. Needs gcc installed via
                                                 apt if a dep has C extensions
  python:3.12-alpine ~50MB      Alpine Linux     musl libc — C-extension wheels
                                                 must compile from source; pain
                                                 with psycopg2, cryptography,
                                                 numpy

After adding app code and packages, expected final image sizes:
  fastapi-single   ~1.0 GB   Dockerfile.single  (full base, single-stage)
  fastapi-slim     ~250 MB   Dockerfile.slim    (slim base, single-stage)
  fastapi-multi    ~200 MB   Dockerfile         (slim base, multi-stage)
  fastapi-alpine   ~100 MB   Dockerfile.alpine  (alpine base, multi-stage)

ALPINE GOTCHA — musl vs glibc:
  Most Python binary wheels are built for glibc (the manylinux standard).
  Alpine uses musl libc. pip can't use those prebuilt wheels on Alpine and
  must compile from source — which requires gcc, musl-dev, etc.

  Result: to get the smallest image, you often have to install a compiler,
  making your build MORE complex, not less. For any app with C-extension
  deps (psycopg2, cryptography, Pillow, numpy), start from slim, not alpine.

RECOMMENDATION:
  python:3.12-slim  for most production Python services
  python:3.12-alpine only if you can verify all deps are pure Python
  python:3.12       only in builder stages or local dev images

### LAYER COMBINING: WHY IT MATTERS

Docker snapshots each layer independently. Even if a later layer deletes
files, those bytes are still in the earlier layer — Docker can't undo them.

WRONG — apt cache survives in layer 2 even though layer 3 cleans it:
  RUN apt-get update                # layer 1: fetches package list
  RUN apt-get install -y gcc        # layer 2: installs + stores cache
  RUN rm -rf /var/lib/apt/lists/*   # layer 3: deletes cache... from layer 3.
                                    # layers 1 and 2 still have it.

RIGHT — cleanup happens inside the same layer, so it's never committed:
  RUN apt-get update && \
      apt-get install -y gcc && \
      rm -rf /var/lib/apt/lists/*   # same layer: cache is never in the image

Same principle for pip:
  --no-cache-dir   prevents pip's download cache from being written at all
  This is better than writing it and then deleting it (which leaves it in a
  prior layer).

Rule: install and clean in the same RUN. Use \ for multi-line readability.

### .DOCKERIGNORE

Docker sends your entire build context (the directory you pass to build) to
the daemon before it executes any Dockerfile instruction. This happens every
build, even before FROM runs.

Excluding large or irrelevant directories speeds up every build and prevents
accidental cache busts (if Docker sees a changed file in the context, it may
invalidate layers even if that file isn't COPYed).

What to always exclude:
  .git/         — your entire git history (can be hundreds of MB)
  .venv/ venv/  — local virtualenv (never needed in an image)
  __pycache__/  — compiled bytecode (regenerated by Python anyway)
  *.pyc *.pyo   — individual bytecache files
  .env          — local env file (never bake secrets into images)
  *.md          — docs
  notes*.py     — practice scripts not needed in the image

The syntax is identical to .gitignore.

### ARG vs ENV

  Feature              ARG (build-time)        ENV (runtime)
  ─────────────────── ──────────────────────── ─────────────────────────────
  When available      Only during `docker build` During build AND at runtime
  In running container No                      Yes
  Override mechanism  --build-arg at build time -e flag at `docker run` time
  Visible in history  Yes (docker history)     Yes
  Safe for secrets    NO                       NO (use secrets/mounts instead)

Common pattern — use ARG to set a default, ENV to propagate it to runtime:
  ARG PORT=8000        ← build-time default
  ENV PORT=${PORT}     ← bakes it into the image as a runtime variable

The running container can still be overridden:
  docker run -e PORT=9001 myimage   ← replaces ENV at runtime

Python ENV vars to set in every image:
  PYTHONDONTWRITEBYTECODE=1   no .pyc files written to disk
  PYTHONUNBUFFERED=1          logs appear immediately in docker logs
  PYTHONFAULTHANDLER=1        better crash tracebacks

### COMMANDS TO RUN

# Build all four variants
docker build -f Dockerfile.single -t fastapi-single .
docker build -f Dockerfile.slim   -t fastapi-slim   .
docker build -t fastapi-multi .
docker build -f Dockerfile.alpine -t fastapi-alpine .

# Compare sizes side by side
docker images | grep fastapi

# Build with custom ARG values
docker build -f Dockerfile.buildargs --build-arg PORT=9000 --build-arg APP_ENV=development -t fastapi-buildargs .

# Run the buildargs image on port 9000
docker run -p 9000:9000 fastapi-buildargs
curl http://localhost:9000

# Override ENV at runtime (regardless of what ARG/ENV said at build time)
docker run -p 8000:8000 -e PORT=8000 fastapi-buildargs

# Inspect what ARG values were baked in (they appear in history)
docker history fastapi-buildargs

# See layers and their sizes for each image
docker history --no-trunc fastapi-single | head -20
docker history --no-trunc fastapi-multi  | head -20

# Confirm the alpine image has no pip at runtime
docker run --entrypoint sh -it fastapi-alpine -c "which pip; echo exit: $?"

# Check that PYTHONUNBUFFERED is set in the buildargs image
docker run --entrypoint sh fastapi-buildargs -c "echo $PYTHONUNBUFFERED"

### LAYER COMBINING EXERCISE

To SEE layers and their individual sizes:
  docker history fastapi-single

Notice layers with "(missing)" — that's normal for base image layers pulled
from a registry; their content is stored but the build context isn't local.
The layers you added (pip install, COPY) will show their sizes clearly.

Try this experiment:
  1. Add a large dummy file inside a RUN in Dockerfile.slim:
       RUN dd if=/dev/urandom of=/tmp/bigfile bs=1M count=100 && rm /tmp/bigfile
  2. Build and check: docker history fastapi-slim
  3. The 100MB is STILL IN THE IMAGE even though it was deleted.
  4. Move the rm into the same RUN:
       RUN dd ... && rm /tmp/bigfile
  5. Rebuild — now that layer is nearly zero bytes.
