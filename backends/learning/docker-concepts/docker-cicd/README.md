# CI/CD with Docker and GitHub Actions

Automate building, tagging, and publishing Docker images in a GitHub Actions workflow.

## Concepts

1. **Why CI builds images** — reproducible builds, tested before deployment, artifacts are immutable
2. **GitHub Actions workflow structure** — triggers, jobs, steps, and environment secrets
3. **GitHub Container Registry (GHCR)** — free image hosting built into GitHub; images live at `ghcr.io/<owner>/<repo>`
4. **BuildKit cache** — `type=gha` caches layers in GitHub Actions cache; `type=registry` caches in the registry itself
5. **`mode=max` vs `mode=min`** — `max` caches all layers including intermediate build stages; `min` caches only the final image (smaller cache, slower for multi-stage builds)

## Files

| File / Folder | Purpose |
|---|---|
| `Dockerfile` | The image to build and publish |
| `app/` | FastAPI app packaged by the Dockerfile |
| `notes_cicd.py` | Annotated notes on all concepts |

## Example workflow (reference)

```yaml
name: Build and push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up BuildKit
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

See `notes_cicd.py` for a breakdown of each step.
