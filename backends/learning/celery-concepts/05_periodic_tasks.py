"""
Concept 05 — Periodic Tasks (Celery Beat)

So far, tasks are triggered by your code calling .delay() or .apply_async().
Celery Beat is a scheduler that *automatically* enqueues tasks on a schedule —
cron jobs, basically, but managed inside Python.

Architecture with Beat:
  Beat process (scheduler)  →  Broker (Redis)  →  Worker(s)
  "every 30s, enqueue X"         (queue)           (run X)

You need TWO processes running:
  - celery worker   (processes tasks)
  - celery beat     (enqueues tasks on a schedule)

Schedules can be defined as:
  - timedelta:   run every N seconds/minutes
  - crontab:     cron-style expressions (minute, hour, day_of_week, etc.)

HOW TO RUN THIS FILE:
  Terminal 1:  docker compose up
  Terminal 2:  celery -A 05_periodic_tasks worker --loglevel=info
  Terminal 3:  celery -A 05_periodic_tasks beat --loglevel=info
  (watch Terminal 2 — tasks will appear on schedule)

  Note: Beat has no "run once and stop" mode. Let it run for a minute
  to see the tasks fire, then Ctrl+C both processes.
"""

from datetime import timedelta
from celery.schedules import crontab
from celery_app import app


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

@app.task
def health_check():
    """Simulates a periodic health check ping."""
    print("[beat] Health check: all systems OK")
    return "ok"


@app.task
def cleanup_expired_sessions():
    """Simulates purging stale sessions from a database."""
    print("[beat] Cleaning up expired sessions...")
    return "cleaned"


@app.task
def generate_daily_report():
    """Simulates generating a daily analytics report."""
    print("[beat] Generating daily report...")
    return "report generated"


@app.task
def sync_external_data(source: str):
    """Parametrized periodic task — demonstrates passing kwargs."""
    print(f"[beat] Syncing data from {source}...")
    return f"synced: {source}"


# ---------------------------------------------------------------------------
# Beat schedule — registered on the Celery app config
# ---------------------------------------------------------------------------
# app.conf.beat_schedule maps a unique name to a schedule definition.
# Each entry needs:
#   "task":     the dotted import path of the task function
#   "schedule": a timedelta or crontab
#   "args"/"kwargs": optional arguments to pass each time it fires

app.conf.beat_schedule = {
    # Run every 10 seconds (good for seeing it work quickly in demos)
    "health-check-every-10s": {
        "task": "05_periodic_tasks.health_check",
        "schedule": timedelta(seconds=10),
    },

    # Run every minute
    "cleanup-sessions-every-minute": {
        "task": "05_periodic_tasks.cleanup_expired_sessions",
        "schedule": timedelta(minutes=1),
    },

    # crontab: every day at 08:00 UTC
    "daily-report-8am": {
        "task": "05_periodic_tasks.generate_daily_report",
        "schedule": crontab(hour=8, minute=0),
    },

    # crontab: every weekday (Mon-Fri) at 09:30 UTC, with kwargs
    "sync-crm-weekday-morning": {
        "task": "05_periodic_tasks.sync_external_data",
        "schedule": crontab(hour=9, minute=30, day_of_week="1-5"),
        "kwargs": {"source": "crm"},
    },

    # crontab: every Sunday at midnight
    "sync-warehouse-weekly": {
        "task": "05_periodic_tasks.sync_external_data",
        "schedule": crontab(hour=0, minute=0, day_of_week="sunday"),
        "kwargs": {"source": "data_warehouse"},
    },
}

# Beat uses UTC by default, consistent with app.conf.enable_utc = True.
# To use local time: app.conf.timezone = "America/New_York"


# ---------------------------------------------------------------------------
# Reference: crontab cheat sheet
# ---------------------------------------------------------------------------
# crontab()                           → every minute
# crontab(minute=0)                   → every hour, on the hour
# crontab(minute=0, hour="*/2")       → every 2 hours
# crontab(minute=30, hour=7,
#         day_of_week="mon-fri")      → 7:30 AM weekdays
# crontab(day_of_month="1",
#         month_of_year="1")          → once a year (Jan 1st)


if __name__ == "__main__":
    print("=" * 60)
    print("CONCEPT 05 — Periodic Tasks (Celery Beat)")
    print("=" * 60)
    print()
    print("This file defines the beat schedule — it doesn't run tasks directly.")
    print()
    print("To see periodic tasks fire:")
    print("  Terminal 1:  docker compose up")
    print("  Terminal 2:  celery -A 05_periodic_tasks worker --loglevel=info")
    print("  Terminal 3:  celery -A 05_periodic_tasks beat --loglevel=info")
    print()
    print("Registered schedules:")
    for name, config in app.conf.beat_schedule.items():
        print(f"  {name}")
        print(f"    task:     {config['task']}")
        print(f"    schedule: {config['schedule']}")
        if "kwargs" in config:
            print(f"    kwargs:   {config['kwargs']}")
