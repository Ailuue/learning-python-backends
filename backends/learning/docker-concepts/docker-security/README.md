# Docker Security & Best Practices

Harden Docker images and containers against common vulnerabilities.

## Concepts

1. **Non-root user** — containers run as root by default; add a dedicated user and switch to it
2. **Read-only filesystem** — mount the container's root filesystem as read-only; only allow writes to specific directories via `tmpfs` or named volumes
3. **Secret management** — never bake secrets into images (`ENV`, `ARG`, or `COPY` of `.env`); use Docker secrets or environment variables injected at runtime
4. **Pinned base image versions** — `FROM python:3.12.3-slim` instead of `FROM python:latest` — reproducible builds, no surprise upgrades
5. **Dockerfile security checklist** — minimize layers, avoid `apt-get upgrade`, remove build tools from the final image

## Files

| File / Folder | Purpose |
|---|---|
| `Dockerfile.insecure` | A Dockerfile with common security mistakes |
| `Dockerfile` | Hardened version of the same app |
| `docker-compose.yml` | Shows read-only and secret patterns |
| `secrets/` | Example Docker secrets (never commit real secrets) |
| `app/` | FastAPI app used as the demo target |

Annotated notes on all the concepts are at the end of this README.

## Key patterns

```dockerfile
# Pin the base image version
FROM python:3.12.3-slim

# Run as a non-root user
RUN useradd --no-create-home appuser
USER appuser

# Never use ENV or ARG to pass secrets — they appear in image layers
# BAD:  ENV DATABASE_URL=postgres://...
# GOOD: inject at runtime via docker run -e or Docker secrets
```

```yaml
# docker-compose.yml — read-only root filesystem
services:
  app:
    read_only: true
    tmpfs:
      - /tmp          # allow writes only to /tmp
```


---

## Docker Security & Best Practices

CONCEPTS:
  1. Run as non-root user
  2. Read-only filesystems
  3. Secret management: never bake secrets into images
  4. Pin base image versions for reproducibility
  5. Dockerfile security checklist

FILES:
  Dockerfile.insecure   6 deliberate security issues (labeled [ISSUE N])
  Dockerfile            secure implementation (labeled [FIX N])
  docker-compose.yml    hardened runtime options
  app/main.py           /whoami and /secrets/check endpoints to verify security
  secrets/              secret files mounted at /run/secrets/ by Compose

### 1. NON-ROOT USER

By default, every Docker container runs as root (uid 0). This means:
  - Any code the container executes has full filesystem write access
  - Vulnerabilities in your app or its dependencies run with root privileges
  - On misconfigured hosts, container root can escape to host root

The fix is a single USER instruction — add it to every Dockerfile:

  RUN groupadd --system --gid 1001 appgroup && \
      useradd  --system --uid 1001 --gid appgroup --no-create-home appuser
  ...
  RUN chown -R appuser:appgroup /app   # must be done while still root
  USER appuser                         # all subsequent steps + runtime = non-root

Verify it worked:
  docker compose run --rm app python -c "import os; print(os.getuid())"
  # 1001 — not 0

  curl http://localhost:8000/whoami
  # {"uid": 1001, "username": "appuser", "is_root": false}

  # Compare with the insecure image:
  docker build -f Dockerfile.insecure -t app-insecure .
  docker run --rm app-insecure python -c "import os; print(os.getuid())"
  # 0 — root!

Ports below 1024 (like 80, 443) require root or the NET_BIND_SERVICE
capability. Apps should listen on 8000+ and let a reverse proxy (nginx,
Traefik) handle 80/443 on the host. We already do this.

Alpine user creation syntax (different from Debian):
  RUN addgroup -g 1001 -S appgroup && \
      adduser  -u 1001 -S appuser -G appgroup

### 2. READ-ONLY FILESYSTEMS

Set in docker-compose.yml:
  services:
    app:
      read_only: true
      tmpfs:
        - /tmp      # grant a writable in-memory filesystem for temp files

What this prevents:
  - Attackers who execute code inside your container cannot write malware
    to the filesystem, install tools, or modify the application
  - Accidental writes (log files accumulating, leaked temp files)

What breaks and how to fix it:
  Python .pyc files      → PYTHONDONTWRITEBYTECODE=1 in ENV
  /tmp usage             → add /tmp to tmpfs
  uvicorn pid files      → add /var/run to tmpfs if needed
  App writing to /app    → use a named volume for the specific path

Test it:
  docker compose run --rm app sh -c "echo test > /app/canary.txt"
  # Read-only file system — write correctly blocked

  docker compose run --rm app sh -c "echo test > /tmp/ok.txt && cat /tmp/ok.txt"
  # test — /tmp is writable via tmpfs

Note: read_only: true is not available in Kubernetes Pod specs (use
securityContext.readOnlyRootFilesystem: true instead).

### 3. SECRET MANAGEMENT

NEVER do these:
  ENV DB_PASSWORD=secret123          ← visible in `docker inspect` forever
  ARG DB_PASSWORD=secret123          ← visible in `docker history` forever
  COPY .env .                        ← bakes .env into the image layer
  COPY secrets/ .                    ← same problem

The problem with ARG specifically:
  Even if you `unset DB_PASSWORD` in a later RUN, the value is stored in
  the layer history. `docker history --no-trunc myimage` shows it in plain
  text. Anyone with read access to the image can see it — today or in 3 years.

THE CORRECT APPROACHES:

  A) Runtime env injection (simplest, good for non-sensitive config)
     Set in docker-compose.yml environment: or via -e flag.
     Visible in `docker inspect` — acceptable for non-secret config.
     NOT acceptable for passwords, API keys, tokens.

  B) Docker secrets — compose secrets: block (what this project uses)
     Mounted at /run/secrets/<name> inside the container.
     The value is a file read by the app at startup.
     NOT in any env var — NOT visible in `docker inspect`.
     In Swarm/Kubernetes: the orchestrator manages the secret store.

     In docker-compose.yml:
       services:
         app:
           secrets:
             - db_password
       secrets:
         db_password:
           file: ./secrets/db_password.txt   # non-Swarm: local file

     In the app:
       with open("/run/secrets/db_password") as f:
           password = f.read().strip()

  C) BuildKit secret mounts (build-time only — e.g. private PyPI token)
     The secret is injected only during one RUN step. Not stored anywhere.

     In the Dockerfile:
       RUN --mount=type=secret,id=pip_token \
           pip install --extra-index-url "$(cat /run/secrets/pip_token)" -r requirements.txt

     When building:
       docker build --secret id=pip_token,src=./secrets/pip_token .

  D) External secret stores (production)
     HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager.
     The app fetches secrets at startup via authenticated API calls.
     Nothing is ever on the local filesystem.

Verify that this project's secrets are NOT in env vars:
  docker compose up -d
  curl http://localhost:8000/secrets/check
  # {"secret_mounted": true, "secret_in_env": false, "secret_length": 36}

  docker inspect docker-security-app-1 | python3 -m json.tool | grep -i secret
  # Shows the mount path — not the value

  # Compare with the insecure image:
  docker build -f Dockerfile.insecure -t app-insecure .
  docker inspect app-insecure | python3 -m json.tool | grep -i "API_KEY\|DB_PASSWORD"
  # Shows the values in plain text in the Config.Env array

### 4. PIN BASE IMAGE VERSIONS

Three levels of pinning:

  Worst:  FROM python:latest
  Pinned by major: FROM python:3.12
  Pinned by patch: FROM python:3.12.8-slim-bookworm      ← minimum for production
  Pinned by digest: FROM python:3.12.8-slim-bookworm@sha256:abc123...  ← maximum

Why the tag alone isn't enough:
  `python:3.12.8-slim-bookworm` is a mutable tag. If the Python team rebuilds
  it (e.g. to patch a glibc CVE), the digest changes but the tag stays the same.
  Your `docker build` on Monday and Tuesday produce different images even though
  the tag looks identical.

  The digest is immutable. Once an image is pushed with a digest, that specific
  combination of layers never changes. Pinning by digest gives you byte-for-byte
  reproducibility across all machines and all time.

Get the digest for any image:
  docker pull python:3.12-slim-bookworm
  docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim-bookworm
  # python:3.12-slim-bookworm@sha256:3a1b2c...

  Then use that in your Dockerfile:
  FROM python:3.12-slim-bookworm@sha256:3a1b2c...

  You can still use the tag alongside for human readability — the digest takes
  precedence:
  FROM python:3.12-slim-bookworm@sha256:3a1b2c...   # tag for humans, digest for builds

Update cadence:
  Pinned digests don't receive security patches automatically. Set a calendar
  reminder to update the digest monthly. Some teams use Dependabot or Renovate
  to automate digest updates.

### 5. IMAGE SCANNING

Before shipping an image, scan it for known CVEs in the OS packages and Python deps.

  # Docker Scout (built into Docker Desktop)
  docker scout cves docker-security-app-1

  # Trivy (open source, excellent)
  brew install trivy
  trivy image docker-security-app-1
  trivy image --severity HIGH,CRITICAL docker-security-app-1

  # In CI — fail the build on critical vulnerabilities
  trivy image --exit-code 1 --severity CRITICAL myapp:latest

  # Scan a Dockerfile before building (catches issues early)
  trivy config Dockerfile

What scanners find:
  - CVEs in OS packages (glibc, openssl, etc. in the base image)
  - Vulnerabilities in Python packages (cross-referenced against PyPI advisory DB)
  - Dockerfile misconfigurations (running as root, no HEALTHCHECK, etc.)
  - Hardcoded secrets in files (some scanners do this too)

Minimal images have fewer CVEs because they have fewer packages:
  python:3.12 (full):           typically 100-300 vulnerabilities
  python:3.12-slim:             typically 20-60 vulnerabilities
  python:3.12-alpine:           typically 5-15 vulnerabilities
  gcr.io/distroless/python3:    typically 0-5 vulnerabilities

Distroless images (Google):
  No shell, no package manager, no standard Linux tools. Extremely small attack
  surface. Trade-off: you can't exec into a distroless container — there's no
  shell to exec into. Use a debug variant (with busybox shell) during development:
    FROM gcr.io/distroless/python3-debian12         # production
    FROM gcr.io/distroless/python3-debian12:debug   # dev (has a shell)

### PRACTICE COMMANDS

# Build and compare images
docker build -f Dockerfile.insecure -t app-insecure .
docker compose build                                  # builds app-secure

# Verify non-root
docker run --rm app-insecure python -c "import os; print('INSECURE uid:', os.getuid())"
docker compose run --rm app python -c "import os; print('SECURE uid:', os.getuid())"

# See the secret baked into the insecure image (visible forever in history)
docker history --no-trunc app-insecure | grep -E "API_KEY|DB_PASSWORD"

# Confirm secret is NOT visible in the secure image's history
docker compose build
docker history docker-security-app   # no secret values visible

# Verify read-only filesystem
docker compose up -d
docker compose exec app sh -c "echo pwned > /app/owned.txt"   # should fail
docker compose exec app sh -c "echo ok > /tmp/ok.txt"         # should succeed (tmpfs)

# Verify secret is accessible but not in env vars
curl http://localhost:8000/secrets/check
# {"secret_mounted": true, "secret_in_env": false, ...}

# Compare docker inspect output: env vars vs secrets
docker compose run -d --name insecure app-insecure  # (won't work cleanly, just conceptual)
docker inspect docker-security-app-1 | python3 -m json.tool | grep -A 5 '"Env"'
# Secure: no secret values in Env array

# Get base image digest for pinning
docker pull python:3.12-slim-bookworm
docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim-bookworm

# Scan for CVEs
docker scout cves docker-security-app-1   # requires Docker Desktop
# or: trivy image docker-security-app-1  (brew install trivy)

### DOCKERFILE SECURITY CHECKLIST

Copy this into a new project and check off each item.

  IMAGE
  [_] Base image pinned to specific version (not :latest, not major-only)
  [_] OS variant explicit (slim-bookworm, alpine — not the full default)
  [_] Digest pinning for byte-for-byte reproducibility (@sha256:...)
  [_] Multi-stage build — build tools absent from runtime image

  SECRETS
  [_] No secrets in ENV or ARG
  [_] No secrets in COPY (secrets/ in .dockerignore)
  [_] Build-time secrets use --mount=type=secret (not ARG)
  [_] .env is in .dockerignore

  FILESYSTEM
  [_] .dockerignore excludes: .git/, .env, secrets/, __pycache__, venv/
  [_] COPY copies specific directories, not COPY . .
  [_] PYTHONDONTWRITEBYTECODE=1
  [_] PYTHONUNBUFFERED=1

  RUNTIME
  [_] Non-root USER created with explicit uid/gid (1001:1001)
  [_] chown run before USER to set app file ownership
  [_] EXPOSE only the port(s) the service actually uses
  [_] HEALTHCHECK defined with sensible interval/timeout/retries

  COMPOSE
  [_] secrets: used for sensitive values (not environment:)
  [_] read_only: true where feasible + tmpfs: for writable paths
  [_] security_opt: ["no-new-privileges:true"]
  [_] cap_drop: [ALL] + cap_add only what's provably needed
  [_] Ports bound to 127.0.0.1 for services not intended to be public
  [_] Internal services (DB, cache) have no ports: in production
  [_] user: "1001:1001" explicit (matches Dockerfile USER)

  SCANNING & MAINTENANCE
  [_] Image scanned with trivy or docker scout before shipping
  [_] CI pipeline fails on HIGH/CRITICAL CVEs
  [_] Calendar reminder to update base image digest monthly
  [_] Dependabot or Renovate configured for automated digest updates
