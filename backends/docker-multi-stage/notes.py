"""
Docker Multi-Stage Builds
=========================

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

--- DOCKERFILE BASICS ---

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

--- LAYER CACHING ---

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

--- MULTI-STAGE STRATEGY ---

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

--- PRACTICE COMMANDS ---

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
  # Inside: ls, python --version, pip list (pip is NOT here — confirm it)
  # Try: which pip   (should fail — pip doesn't exist in the runtime stage)

# 7. Layer cache demo — experience the caching speedup
#    Edit app/main.py (change the "message" string in root())
#    Then rebuild:
docker build -t fastapi-multi .
#    Watch for "CACHED" on the pip install step — deps didn't change,
#    so Docker skips that layer entirely. Only the COPY app/ layer reruns.

# 8. CMD override at runtime
docker run fastapi-multi uvicorn main:app --host 0.0.0.0 --port 8000 --reload
#    The CMD is replaced entirely. The image still works, just with --reload.

--- THINGS TO NOTICE ---

- fastapi-single is ~1GB, fastapi-multi is ~200MB (roughly 5x smaller)
- `docker history` shows fastapi-multi has far fewer layers
- pip is absent from the multi-stage runtime container
- Rebuilding after a code change reuses the pip install layer (CACHED)
- The .dockerignore prevents notes.py and __pycache__ from entering the
  build context, keeping things clean and preventing accidental cache busts
"""


def layer_caching_reminder():
    print("Layer caching rule:")
    print("  Things that change RARELY  → early in the Dockerfile")
    print("  Things that change OFTEN   → late in the Dockerfile")
    print()
    print("For Python: requirements.txt before app code.")
    print("Changing one line of app code should NOT re-run pip install.")


def size_comparison_expected():
    print("Expected image sizes after building both:")
    print("  fastapi-single   ~1.0 GB  (python:3.12 full base)")
    print("  fastapi-multi    ~200 MB  (python:3.12-slim + venv only)")
    print()
    print("Run: docker images | grep fastapi")


if __name__ == "__main__":
    layer_caching_reminder()
    print()
    size_comparison_expected()
