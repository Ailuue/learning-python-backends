# =============================================================================
# MULTI-STAGE DOCKERFILE — smaller, cleaner, production-ready
#
# Problem: build tools (pip, compilers, wheel building) are needed at build
# time but waste space at runtime. A running FastAPI app doesn't need pip.
#
# Solution: use two stages.
#   Stage 1 (builder): full image, install everything into a virtual env
#   Stage 2 (runtime): slim image, copy ONLY the venv from stage 1
#
# The final image has no pip, no compiler, no build cache — just your app
# and its installed packages.
#
# Build: docker build -t fastapi-multi .
# Run:   docker run -p 8000:8000 fastapi-multi
# =============================================================================


# =============================================================================
# STAGE 1: builder
# =============================================================================
# AS builder — names this stage so stage 2 can reference it with COPY --from=
FROM python:3.12 AS builder

WORKDIR /build

# Create a virtual environment inside the image. Installing into a venv
# (rather than the system Python) makes it trivial to copy just the packages
# to the next stage — it's one self-contained directory.
RUN python -m venv /opt/venv

# Activate the venv for all subsequent RUN commands in this stage.
ENV PATH="/opt/venv/bin:$PATH"

# Cache the expensive pip install layer separately from the app code.
# requirements.txt changes rarely; app code changes constantly.
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# =============================================================================
# STAGE 2: runtime
# =============================================================================
# python:3.12-slim — stripped-down image, ~130MB vs ~900MB for the full image.
# No build tools, no apt package lists, no compilers. Just Python and the OS.
FROM python:3.12-slim AS runtime

# Copy the venv from stage 1. Nothing else from the builder comes along —
# no pip, no build cache, no compiler artifacts.
COPY --from=builder /opt/venv /opt/venv

# Activate the copied venv.
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY app/ .

EXPOSE 8000

# CMD vs ENTRYPOINT:
#
# CMD ["uvicorn", "main:app", ...]
#   Sets the default command. Fully replaceable at runtime:
#   docker run fastapi-multi bash   ← replaces CMD entirely
#
# ENTRYPOINT ["uvicorn"]
#   Sets the fixed executable. Runtime args are APPENDED, not replaced:
#   docker run fastapi-multi main:app --reload   ← appends to entrypoint
#
# CMD is more flexible for dev. ENTRYPOINT is better when the image has
# exactly one purpose and you want to prevent users from running anything else.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
