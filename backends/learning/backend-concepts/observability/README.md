# Observability: Logs, Metrics, and Correlation IDs

## What is this?

You've built an app. It's running in production. Something goes wrong — a user reports an error, or requests suddenly get slow. How do you figure out what happened?

**Observability** is the ability to understand what your system is doing from the outside, by looking at the data it produces. The three main signals are:

**Logs** — a record of things that happened. "User 42 placed order 99." Good logs are structured (JSON), not just plain text, so you can search and filter them: *show me all errors for user 42 in the last hour*.

**Metrics** — numbers that change over time. How many requests per second? What's the p95 response time? How many errors in the last 5 minutes? Metrics are cheap to store and great for dashboards and alerts.

**Traces** — the path a single request took through your system. Especially useful in microservices when a request touches 5 different services and you need to find which one is slow.

These three signals are sometimes called the "three pillars of observability."

## Why it matters

Without observability, debugging production is guesswork. With it, you can answer questions like:
- Which endpoint is responsible for the spike in errors?
- What was this specific user doing when they got a 500?
- Did my deploy make things faster or slower?
- How close am I to my database connection limit?

## What the files cover

| File | What it teaches |
|---|---|
| `01_structured_logging.py` | Why JSON logs beat plain text; how to attach context (request ID, user ID) to every log line automatically |
| `02_metrics.py` | The three metric types — Counter, Histogram, Gauge — and how to expose them for Prometheus |
| `03_combined.py` | A production-style FastAPI app combining all three, with a correlation ID that threads through every log line for a request |
| `prometheus.yml` | Tells Prometheus where to scrape metrics from |
| `docker-compose.yml` | Runs Prometheus + Grafana locally for a full dashboard setup |

## How to run

```bash
pip install -r requirements.txt

# Standalone logging demo:
python 01_structured_logging.py

# Metrics demo (then curl http://localhost:8000/metrics):
uvicorn 02_metrics:app --reload

# Full stack — app + Prometheus + Grafana:
uvicorn 03_combined:app --reload        # terminal 1
docker compose up -d                    # terminal 2

# Open http://localhost:9090 for Prometheus
# Open http://localhost:3000 for Grafana (admin/admin)
# Add data source: Connections → Prometheus → URL: http://prometheus:9090
```
