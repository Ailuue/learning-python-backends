# Reverse Proxy with nginx

Put nginx in front of a FastAPI app using Docker Compose.

## Concepts

1. **What a reverse proxy does** — accepts public traffic and forwards it to one or more backend services; the backend never exposes a port directly to the internet
2. **nginx `upstream` block** — names a backend service; the service name from `docker-compose.yml` is the hostname
3. **`proxy_set_header`** — forwarding the real client IP and other headers to the backend
4. **`expose` vs `ports`** — `expose` makes a port reachable to other containers on the same network; `ports` maps it to the host. The app should use `expose`, nginx uses `ports`
5. **Path-based routing** — route `/api/` to one service and `/` to another

## Files

| File / Folder | Purpose |
|---|---|
| `docker-compose.yml` | App + nginx services |
| `nginx/` | nginx config files |
| `app/` | FastAPI backend (only reachable via nginx) |
| `notes_reverseproxy.py` | Annotated notes on all concepts |

## Try it

```bash
docker compose up --build
# nginx listens on port 80
curl http://localhost/          # routed to FastAPI
curl http://localhost/health    # routed to FastAPI health check
```

## Core nginx config pattern

```nginx
upstream app {
    server app:8000;   # "app" is the Docker Compose service name
}

server {
    listen 80;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## expose vs ports in docker-compose.yml

```yaml
services:
  app:
    expose: ["8000"]    # only reachable by nginx, not the host machine

  nginx:
    ports: ["80:80"]    # the only service exposed to the host
```
