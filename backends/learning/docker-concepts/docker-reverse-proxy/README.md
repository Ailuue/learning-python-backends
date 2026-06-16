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

Annotated notes on all the concepts are at the end of this README.

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


---

## Reverse Proxy Pattern with nginx

CONCEPTS:
  1. What a reverse proxy is and why you use one
  2. nginx upstream block: naming a backend
  3. proxy_set_header: forwarding the real client IP
  4. expose: vs ports: — the critical distinction
  5. Routing by path: nginx as a router in front of multiple services

### WHAT IS A REVERSE PROXY?

A reverse proxy sits in front of one or more backend services.
Clients talk to the proxy; the proxy forwards requests to the right backend.

  Client → nginx (port 80) → app (port 8000, internal only)

The client never talks to the app directly. The client only knows about nginx.

WHY USE ONE?

  - Hide internal ports: your app container is never exposed to the internet
  - TLS termination: nginx handles HTTPS, your app speaks plain HTTP
  - Path-based routing: /api/* → api service, /* → frontend service
  - Static file serving: nginx serves /static/* itself without hitting the app
  - Rate limiting and caching: nginx has built-in support for both
  - Load balancing: nginx round-robins across multiple app instances

### expose: vs ports:

ports:                         expose:
  - "80:80"                      - "8000"

  Publishes to host machine.     Documents the port only.
  curl localhost:80 works.       Does NOT publish to host.
  ANY process on your host       Only other containers on the
  can reach it.                  same Docker network can reach it.

In this project:
  nginx has   ports: ["80:80"]   → reachable from your host at localhost:80
  app has     expose: ["8000"]   → NOT reachable from your host at all

Try it:
  curl localhost       # works — nginx answers, proxies to app
  curl localhost:8000  # connection refused — app port is not published

### nginx UPSTREAM BLOCK

upstream app {
    server app:8000;
}

"app" in server app:8000 is the Compose SERVICE NAME.
Docker DNS resolves it to the app container's internal IP automatically.
You can add more servers for load balancing:

upstream app {
    server app:8000;
    server app2:8000;   # if you docker compose up --scale app=2
}

### PROXY HEADERS

Without header forwarding, your FastAPI app sees:
  request.client.host  → nginx's internal Docker IP (e.g. 172.18.0.3)
  Host header          → "app:8000"  (the upstream address)

With proxy_set_header:
  X-Real-IP            → the original client's IP
  X-Forwarded-For      → comma-separated chain of proxies + client IP
  X-Forwarded-Proto    → "http" or "https" (useful for redirect logic)
  Host                 → the original Host header from the client

In FastAPI, read them from request.headers:
  request.headers.get("X-Real-IP")
  request.headers.get("X-Forwarded-For")

In production with multiple proxy layers, X-Forwarded-For is a list:
  "203.0.113.1, 10.0.0.1"   ← client IP first, each proxy appends its own

### PATH-BASED ROUTING

nginx can route to different services based on URL path:

server {
    listen 80;

    location /api/ {
        proxy_pass http://api_service;   # FastAPI backend
    }

    location /static/ {
        root /var/www;                   # served by nginx directly (no app hit)
    }

    location / {
        proxy_pass http://frontend;      # React / Next.js frontend
    }
}

Each service is a separate Compose service; nginx is the single entry point.
This is how production stacks like Next.js + FastAPI + static assets are wired.

### FILES IN THIS PROJECT

  Dockerfile              multi-stage build, non-root user, no EXPOSE
  nginx/default.conf      upstream block + proxy_set_header config
  docker-compose.yml      nginx (ports: 80:80) + app (expose: 8000 only)
  app/main.py             FastAPI returning proxy headers in responses

### COMMANDS

# Build and start
docker compose up --build

# Confirm app is NOT reachable directly
curl localhost:8000        # should fail: connection refused

# Confirm nginx proxies correctly
curl localhost             # should return JSON from FastAPI
curl localhost/headers     # shows all headers nginx forwarded

# Watch nginx access logs
docker compose logs -f nginx

# Scale the app (nginx round-robins automatically)
docker compose up -d --scale app=3
curl localhost             # requests distributed across 3 app containers

# Shell into nginx container to inspect config
docker compose exec nginx sh
nginx -T                   # dump full resolved config

### PRACTICE EXERCISES

1. Confirm the proxy is hiding the app:
     docker compose up --build -d
     curl localhost          # works — nginx proxies to app
     curl localhost:8000     # connection refused — app not exposed

2. Inspect proxy headers:
     curl localhost/headers  # see X-Real-IP, X-Forwarded-For, Host
     Note: X-Real-IP will show 172.x.x.x (Docker bridge IP on Mac),
           not your actual machine IP, because Docker NATs the connection.

3. Watch nginx logs:
     docker compose logs -f nginx
     curl localhost/health
     curl localhost/
     # Each request shows in access_log with status code and bytes

4. Test health check ordering:
     docker compose down
     docker compose up
     # Watch: app starts → health check passes → only THEN nginx starts
     # nginx depends_on app with condition: service_healthy

5. Break it and fix it:
     # In nginx/default.conf, change "server app:8000" to "server app:9999"
     # docker compose up --build
     # curl localhost → 502 Bad Gateway (nginx can't reach app)
     # Fix the port, rebuild, watch it recover

6. Add path-based routing:
     # In nginx/default.conf, add a /health location that nginx handles:
     location /health {
         return 200 '{"status":"nginx ok"}\n';
         add_header Content-Type application/json;
     }
     # Requests to /health never hit the FastAPI app — nginx handles them.
