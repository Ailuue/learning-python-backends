# GitHub Actions

## What is this?

GitHub Actions is GitHub's built-in CI/CD platform. Every workflow is a YAML file in `.github/workflows/`. GitHub runs these automatically on the triggers you define — pushes, PRs, tags, schedules, or manual dispatch.

This module covers the four workflow patterns every backend engineer needs:

| Concept | Workflow file | Notes file |
|---|---|---|
| CI pipeline — lint + test matrix | `.github/workflows/ci.yml` | `01_ci_pipeline.py` |
| Releases from version tags | `.github/workflows/release.yml` | `02_release.py` |
| Scheduled jobs + manual dispatch | `.github/workflows/scheduled.yml` | `03_scheduled.py` |
| Environments + deployment gates | (illustrative) | `04_environments.py` |
| Reusable workflows | (illustrative) | `05_reusable_workflows.py` |

The first three have live workflow files that will run on this repo. The last two are concept notes with annotated YAML examples — they require external deployment infrastructure to actually run.

> **See also:** `.github/workflows/docker-cicd.yml` + `docker-concepts/docker-cicd/notes_cicd.py` for Docker build/push patterns.

## How Actions are structured

```
.github/
  workflows/
    ci.yml          ← runs on push/PR
    release.yml     ← runs on v* tags
    scheduled.yml   ← runs on cron + manual dispatch
    docker-cicd.yml ← builds and pushes Docker images

Every workflow file has:
  name:       display name in the Actions UI
  on:         trigger(s)
  jobs:
    job-name:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - run: some-command
```

## Quick reference

```bash
# Trigger a manual run from the CLI (requires gh CLI + auth)
gh workflow run scheduled.yml

# Watch a run in progress
gh run watch

# View workflow run history
gh run list --workflow ci.yml

# Push a release tag to trigger release.yml
git tag v1.0.0
git push origin v1.0.0
```
