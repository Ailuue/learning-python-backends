# Celery Deep Dive

> 📚 [Backend Learning](../README.md) · **Specialized topic** — best after the core path.

Background job processing with Celery and Redis.

## Architecture

```
Producer (your code)
    │
    │  .delay() / .apply_async()
    ▼
Broker (Redis :6379/0)   ← task queue
    │
    │  worker picks up task
    ▼
Worker (celery worker)
    │
    │  stores result
    ▼
Result Backend (Redis :6379/1)
    │
    │  .get() / .state
    ▼
Producer reads result
```

Flower (web UI) connects to the broker and lets you inspect queues, workers, and task history at http://localhost:5555.

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis + Flower
docker compose up
```

## Concept files

| File | Concept | Worker command |
|------|---------|----------------|
| [01_basic_tasks.py](01_basic_tasks.py) | Define tasks, `delay()`, `apply_async()`, fire-and-forget | `celery -A 01_basic_tasks worker --loglevel=info` |
| [02_task_states.py](02_task_states.py) | State machine, `update_state()`, custom progress, FAILURE | `celery -A 02_task_states worker --loglevel=info` |
| [03_retries.py](03_retries.py) | `autoretry_for`, `self.retry()`, exponential backoff, jitter | `celery -A 03_retries worker --loglevel=info` |
| [04_workflows.py](04_workflows.py) | `chain`, `group`, `chord`, `.s()` vs `.si()` | `celery -A 04_workflows worker --loglevel=info --concurrency=4` |
| [05_periodic_tasks.py](05_periodic_tasks.py) | Celery Beat, `timedelta`, `crontab` schedules | See below |

## Running each concept

Each file follows the same pattern:

```
Terminal 1 (once):  docker compose up
Terminal 2:         celery -A <module_name> worker --loglevel=info
Terminal 3:         python <module_name>.py
```

### Concept 05 (Beat) is different — needs two background processes:

```
Terminal 2:  celery -A 05_periodic_tasks worker --loglevel=info
Terminal 3:  celery -A 05_periodic_tasks beat --loglevel=info
```

Watch Terminal 2 for tasks arriving on schedule. The `health_check` task fires every 10 seconds so you'll see it quickly.

## Key concepts at a glance

### Task calling modes
```python
add(2, 3)                      # synchronous — no broker, no worker
add.delay(2, 3)                # async — returns AsyncResult immediately
add.apply_async(args=[2, 3],   # async with options
    countdown=10,              #   run after 10s delay
    eta=datetime(2026, 1, 1),  #   or at a specific time
    expires=60,                #   discard if not run within 60s
)
```

### Task states
```
PENDING → STARTED → SUCCESS
                  ↘ FAILURE
                  ↘ RETRY
                  ↘ REVOKED
```
Any task ID not in the result backend reports PENDING — including IDs that don't exist.

### Retry pattern
```python
@app.task(bind=True, max_retries=3)
def my_task(self):
    try:
        risky_operation()
    except SomeError as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Workflow primitives
```python
# Sequential: a → b → c (each result feeds the next)
chain(a.s(x), b.s(), c.s()).delay()

# Parallel: a, b, c run concurrently
group(a.si(x), b.si(y), c.si(z)).delay()

# Parallel + collect: a, b, c run, then callback([ra, rb, rc])
chord(group(a.si(x), b.si(y)), callback.s()).delay()
```

`.s()` = mutable signature (passes previous result as first arg)
`.si()` = immutable signature (ignores previous result)

### Beat schedule
```python
app.conf.beat_schedule = {
    "my-job": {
        "task": "module.task_name",
        "schedule": timedelta(minutes=5),       # every 5 min
        # "schedule": crontab(hour=8, minute=0), # daily at 08:00
        "kwargs": {"param": "value"},
    },
}
```
