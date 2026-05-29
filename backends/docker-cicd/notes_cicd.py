"""
CI/CD Integration — Docker Build in GitHub Actions
=====================================================

CONCEPTS:
  1. Why CI builds images instead of deploying source code
  2. GitHub Actions workflow structure for Docker
  3. GitHub Container Registry (GHCR) — free image hosting built into GitHub
  4. type=gha cache vs type=registry cache — when to use each
  5. mode=max vs mode=min — how much to cache
  6. Image tags vs digests — why production deploys should use digests
  7. Build args — baking git SHA into the image at build time

--- WHY BUILD IN CI? ---

Local build → push → server pulls:
  WRONG. The image on the server was built on your laptop with your local env.
  It might work differently than what CI would produce.

CI build → push → server pulls:
  RIGHT. The image on the server is identical to what CI verified.
  "The image built in CI is what gets deployed" means this exact binary.

The git SHA baked into the image proves it: curl /version on any server
and compare the SHA to the GitHub Actions run that produced that image.

--- WORKFLOW STRUCTURE ---

Trigger:
  push to main, or PR — scoped to paths so only relevant changes run it.

Jobs:
  build  (ubuntu-latest, ~free for public repos, 2000 min/month free for private)

Key steps:
  1. actions/checkout@v4           — clone the repo
  2. docker/setup-buildx-action@v3 — enable BuildKit (required for caching)
  3. docker/login-action@v3        — authenticate to GHCR with GITHUB_TOKEN
  4. docker/metadata-action@v5     — generate tags from git refs
  5. docker/build-push-action@v6   — build + cache + push

--- GITHUB CONTAINER REGISTRY (GHCR) ---

Free tier: unlimited pulls for public repos, 500 MB storage + 1 GB transfer free
           for private repos (then $0.008/GB-month storage, $0.50/GB transfer)

Image names follow this pattern:
  ghcr.io/<github-owner>/<repo-name>/<image-name>:<tag>

For this repo (Ailuue/learning-python-backends):
  ghcr.io/ailuue/learning-python-backends/docker-cicd:latest
  ghcr.io/ailuue/learning-python-backends/docker-cicd:sha-abc1234

Authentication:
  GITHUB_TOKEN is automatically provided by GitHub Actions.
  It needs `permissions: packages: write` in the job (already set in the workflow).
  No manual secrets needed.

Pull a built image locally:
  docker pull ghcr.io/ailuue/learning-python-backends/docker-cicd:latest
  docker run -p 8000:8000 ghcr.io/ailuue/learning-python-backends/docker-cicd:latest
  curl localhost:8000/version   # build_sha matches the commit

--- CACHING: type=gha vs type=registry ---

type=gha  (GitHub Actions Cache):
  Stores BuildKit layer cache in GitHub's built-in cache (up to 5 GB per repo).
  Cache key is computed automatically from layer content.
  Evicted by GitHub after 7 days of no access (LRU when over 5 GB).
  FASTEST for GitHub Actions — tight integration, no network round-trip to a registry.
  ONLY works inside GitHub Actions — can't reuse from a local build.

  cache-from: type=gha
  cache-to:   type=gha,mode=max

type=registry  (Registry-based Cache):
  Stores cache layers as a separate image in your container registry.
  Works anywhere — GitHub Actions, local buildx, any CI system.
  Slower than type=gha (registry download vs GitHub cache).
  Useful if you want a local build to reuse CI's cache layers.

  cache-from: type=registry,ref=ghcr.io/ailuue/learning-python-backends/docker-cicd:cache
  cache-to:   type=registry,ref=ghcr.io/ailuue/learning-python-backends/docker-cicd:cache,mode=max

Use type=gha unless you need cross-environment cache sharing.

--- mode=max vs mode=min ---

mode=min  (default):
  Caches only the final stage layers.
  Builder stage (pip install, gcc compile, etc.) is NOT cached.
  Smaller cache, but every build still runs the builder-stage steps.

mode=max:
  Caches ALL layers from ALL stages, including intermediate builder stages.
  The pip install layer is cached even though it's not in the final image.
  Larger cache, but subsequent builds skip pip install entirely.
  Always use mode=max in CI.

--- IMAGE TAGS vs DIGESTS ---

Tag (mutable):
  ghcr.io/ailuue/learning-python-backends/docker-cicd:latest
  "latest" can be rewritten on every push. There's no guarantee that
  the "latest" you deployed yesterday is the same as "latest" today.

Digest (immutable):
  ghcr.io/ailuue/learning-python-backends/docker-cicd@sha256:abc123...
  This is a content-addressable hash of the exact image layers.
  It will NEVER change. Pull the same digest in 6 months → same binary.

In production deploy steps:
  WRONG:  docker pull image:latest   (unknown which version)
  RIGHT:  docker pull image@sha256:abc123  (known, verifiable, immutable)

The "Image digest" step in the workflow prints this for every push.

--- BUILD ARGS AND LAYER CACHE ORDER ---

ARG BUILD_SHA=local-build
ENV BUILD_SHA=$BUILD_SHA

This is placed AFTER the COPY of requirements and the pip install.
If it were placed before, every new commit SHA would bust the pip cache,
because Docker re-runs all layers after the first changed one.

Late placement means: pip install is cached per requirements.txt content,
and only the final layers change when the SHA changes.

--- EXERCISES ---

1. Push and watch it run:
     git add .github/workflows/docker-cicd.yml backends/docker-cicd/
     git commit -m "feat: add CI/CD pipeline for docker-cicd app"
     git push
   Open: https://github.com/Ailuue/learning-python-backends/actions
   Watch the "Docker Build & Push" workflow run.

2. Pull and run the CI-built image:
     docker pull ghcr.io/ailuue/learning-python-backends/docker-cicd:latest
     docker run -p 8000:8000 ghcr.io/ailuue/learning-python-backends/docker-cicd:latest
     curl localhost:8000/version
   Compare build_sha to the SHA of your commit on GitHub.

3. See caching in action:
   Push the same commit twice (amend then force-push a whitespace change).
   First run: all layers are built from scratch.
   Second run: "CACHED" appears next to every layer that didn't change.
   The pip install step should be fully cached on the second run.

4. Compare build time: first run vs cached run.
   GitHub Actions shows step timing — check the "Build and push" step.

5. Try mode=min vs mode=max:
   Change cache-to to mode=min, push, observe cache size and hit rate.
   Change back to mode=max.

6. Make the image private vs public:
   After the first push, go to your package on GitHub:
   https://github.com/Ailuue?tab=packages
   By default it may be private. You can make it public there.

--- WHERE TO GO NEXT ---

  Deploy step: add a step after build-push that SSHs to a server and
    runs: docker pull image@$DIGEST && docker stop old && docker run new

  Multi-environment: build once, promote the same digest through
    staging → production (never rebuild between envs)

  Vulnerability scanning: add trivy-action after build to scan the image
    before pushing:
    uses: aquasecurity/trivy-action@master
    with:
      image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
"""

WORKFLOW_STEPS = [
    "actions/checkout@v4 — clone repo",
    "docker/setup-buildx-action@v3 — enable BuildKit",
    "docker/login-action@v3 — GHCR auth with GITHUB_TOKEN",
    "docker/metadata-action@v5 — generate tags from git refs",
    "docker/build-push-action@v6 — build, cache, push",
]

CACHE_TYPES = {
    "type=gha": "GitHub Actions cache — fastest in GH Actions, not portable",
    "type=registry": "Registry-based — portable across environments",
}
