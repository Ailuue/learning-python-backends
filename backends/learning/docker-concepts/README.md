# Docker Concepts

Hands-on Docker modules, from the basics of multi-stage builds to production patterns like reverse proxying and CI/CD.

## Modules

| Folder | What it covers |
|---|---|
| [docker-multi-stage/](docker-multi-stage/) | Dockerfile basics, multi-stage builds, layer caching, image size comparison |
| [docker-compose/](docker-compose/) | Multi-service setups, named volumes, health checks, `.env` files |
| [docker-debugging/](docker-debugging/) | `docker exec`, `docker logs`, `docker inspect`, resource limits, fixing a broken container |
| [docker-reverse-proxy/](docker-reverse-proxy/) | nginx upstream blocks, `proxy_set_header`, `expose` vs `ports`, path-based routing |
| [docker-security/](docker-security/) | Non-root users, read-only filesystems, secret management, pinned base images |
| [docker-cicd/](docker-cicd/) | Building and pushing images in GitHub Actions, GHCR, BuildKit cache strategies |

## Suggested order

1. `docker-multi-stage` — understand Dockerfiles before composing multiple services
2. `docker-compose` — wire services together
3. `docker-debugging` — learn to inspect running containers
4. `docker-reverse-proxy` — put nginx in front of your app
5. `docker-security` — harden what you've built
6. `docker-cicd` — automate the build and publish pipeline
