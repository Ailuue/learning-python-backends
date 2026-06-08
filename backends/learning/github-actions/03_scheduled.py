"""
Scheduled Workflows — .github/workflows/scheduled.yml
=======================================================

CONCEPTS:
  1. Cron syntax and UTC timing
  2. workflow_dispatch — the "Run workflow" button
  3. Typed inputs: boolean, choice, string
  4. Accessing inputs with defaults for scheduled runs
  5. Conditional steps (if:)
  6. Idempotency — why scheduled jobs must be safe to re-run
  7. When to use scheduled workflows vs external cron services

--- CRON SYNTAX ---

GitHub's schedule uses standard POSIX cron syntax. All times are UTC.

    ┌──────────── minute        (0-59)
    │ ┌────────── hour          (0-23)
    │ │ ┌──────── day of month  (1-31)
    │ │ │ ┌────── month         (1-12)
    │ │ │ │ ┌──── day of week   (0-6, Sun=0)
    │ │ │ │ │
    * * * * *

Common patterns:
  "0 9 * * 1"     Monday 09:00 UTC (GitHub's runners are UTC)
  "0 */6 * * *"   Every 6 hours, on the hour
  "30 2 * * *"    Daily at 02:30 UTC
  "0 0 1 * *"     First day of each month at midnight UTC
  "0 8-17 * * 1-5" Every hour, business hours Mon-Fri UTC

IMPORTANT: GitHub may delay scheduled runs by up to 15 minutes under high
runner load. Don't use this for sub-minute precision or time-critical jobs.
For those, use an external scheduler (AWS EventBridge, Render cron jobs, etc.).

Also: scheduled workflows on branches other than the default branch
(usually main) are silently not run. They only run on the default branch.

--- workflow_dispatch ---

Adds a "Run workflow" button to the Actions tab and enables gh CLI triggers.

    on:
      workflow_dispatch:

With no inputs block, the button just fires the workflow.
With inputs, the UI shows form fields.

    on:
      workflow_dispatch:
        inputs:
          environment:
            description: "Deploy target"
            type: choice
            options: [staging, production]
            default: staging
          dry_run:
            description: "Dry run — no side effects"
            type: boolean
            default: true

Input types:
  string    free-text input
  boolean   checkbox (true/false)
  choice    dropdown from options list
  number    numeric input (string under the hood, validate yourself)
  environment  dropdown from repo environments (for deploy workflows)

Access inputs: ${{ inputs.environment }}, ${{ inputs.dry_run }}

--- INPUTS ARE EMPTY ON SCHEDULED RUNS ---

When the workflow triggers via schedule, github.event.inputs is empty.
github.event_name is "schedule" instead of "workflow_dispatch".

Use the || operator to supply defaults:
  ${{ inputs.python_version || '3.13' }}
  ${{ inputs.dry_run || 'false' }}

This lets one workflow handle both scheduled and manual runs.

--- CONDITIONAL STEPS ---

    - name: Notify on failure
      if: failure()          # only runs if any previous step failed

    - name: Post to Slack
      if: success() && github.event_name == 'schedule'

    - name: Skip in dry run
      if: inputs.dry_run != 'true'

Context functions available in if:
  success()   all previous steps succeeded
  failure()   any previous step failed
  cancelled() the workflow was cancelled
  always()    run regardless (useful for cleanup)

Combine conditions: if: failure() && github.ref == 'refs/heads/main'

--- TRIGGERING MANUALLY ---

From the GitHub UI:
  Actions tab → select workflow → "Run workflow" button → fill in inputs → Run

From the gh CLI:
  gh workflow run scheduled.yml
  gh workflow run scheduled.yml -f dry_run=false -f python_version=3.11

  Watch the run:
  gh run watch

  List recent runs:
  gh run list --workflow scheduled.yml

--- IDEMPOTENCY ---

A scheduled job must be safe to run multiple times with the same effect.

BAD — not idempotent:
  - Inserts a row every time it runs → database fills with duplicates
  - Sends an email every time it runs → users get spammed
  - Increments a counter → wrong results if retried

GOOD — idempotent:
  - "Run tests and report status" → same output every time
  - "Clean up files older than 7 days" → re-running does nothing new
  - "Upsert (INSERT OR REPLACE) a status record" → same end state

GitHub might re-run a failed scheduled job, or you might trigger it manually.
If your job is not idempotent, re-runs cause problems.

--- WHEN TO USE SCHEDULED WORKFLOWS vs EXTERNAL CRON ---

Use GitHub Actions schedule when:
  - The job works with repo code (tests, docs generation, dependency checks)
  - You don't need sub-minute precision
  - You don't need guaranteed execution time (15-minute delay is acceptable)
  - The repo is on GitHub (not self-hosted elsewhere)

Use an external scheduler (AWS EventBridge, Render, Railway, fly.io) when:
  - You need reliable, punctual execution (financial operations, SLA-bound tasks)
  - The job interacts with production infrastructure (deploy, DB maintenance)
  - You want the schedule to run even if nobody pushes to the repo
    (GitHub disables scheduled workflows after 60 days of repo inactivity)
  - You need retry logic with backoff

--- EXERCISES ---

1. Trigger manually with the gh CLI:
     gh workflow run scheduled.yml -f dry_run=true -f python_version=3.12
     gh run watch

2. Observe the dry_run conditional:
   Change the workflow so a step only runs when dry_run is false.
   Run manually with dry_run=true — the step should be skipped.
   Run with dry_run=false — it should run.

3. Add a matrix to the scheduled run:
   Replace the single python_version input with a matrix:
     strategy:
       matrix:
         python-version: ["3.11", "3.12", "3.13"]
   Observe: one scheduled run checks all three versions in parallel.

4. Simulate a failure notification:
   Temporarily add `exit 1` to the test step. Trigger manually.
   The "Report failure" step should run (if: failure()).
   Remove the `exit 1` and re-trigger — the failure step should be skipped.

5. Add a Slack notification (optional):
   Store a Slack webhook URL as a repo secret named SLACK_WEBHOOK.
   Replace the echo in "Report failure" with:
     curl -X POST ${{ secrets.SLACK_WEBHOOK }} \\
       -H 'Content-type: application/json' \\
       -d '{"text":"Health check failed on ${{ github.repository }}"}'
"""

CRON_EXAMPLES = {
    "every_monday_9am_utc":     "0 9 * * 1",
    "every_6_hours":            "0 */6 * * *",
    "daily_midnight_utc":       "0 0 * * *",
    "first_of_month_2am_utc":   "0 2 1 * *",
    "weekdays_business_hours":  "0 8-17 * * 1-5",
}

INPUT_TYPES = {
    "string":      "Free-text input field",
    "boolean":     "Checkbox — true or false",
    "choice":      "Dropdown from a predefined options list",
    "number":      "Numeric field (validated by the UI, string in expressions)",
    "environment": "Dropdown from repo environments (deploy workflows)",
}

CONDITIONAL_FUNCTIONS = {
    "success()":    "All previous steps passed",
    "failure()":    "Any previous step failed",
    "cancelled()":  "Workflow was manually cancelled",
    "always()":     "Run regardless of previous step outcomes (cleanup)",
}
