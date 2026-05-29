import os

from fastapi import FastAPI

app = FastAPI(title="CI/CD Practice API")

# Injected at build time via ARG → ENV in the Dockerfile.
# Local builds show "local-build"; CI builds show the exact git SHA.
BUILD_SHA = os.environ.get("BUILD_SHA", "local-build")


@app.get("/")
def root():
    return {"message": "Hello from CI/CD!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/version")
def version():
    """
    Proves the CI-built image is what's running.
    Compare this SHA to the commit shown in the GitHub Actions run.
    """
    return {
        "build_sha": BUILD_SHA,
        "is_ci_build": BUILD_SHA != "local-build",
    }
