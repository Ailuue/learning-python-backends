"""
Environments & Deployment Gates
=================================

CONCEPTS:
  1. GitHub Environments — named deployment targets with their own secrets
  2. Protection rules — required reviewers, wait timers, branch restrictions
  3. Deployment logs — the "Environments" section on the repo homepage
  4. Secrets vs Variables — when to use each
  5. Multi-environment deploy pattern: build once, promote through envs
  6. environment: input type for workflow_dispatch

--- WHAT IS A GITHUB ENVIRONMENT? ---

A GitHub Environment is a named deployment target (e.g. "staging", "production")
that can have:
  - Its own set of secrets and variables (different DB URLs per env)
  - Protection rules (require a human to approve before the job runs)
  - Deployment history visible on the repo homepage

Without environments: any job can access any secret.
With environments: the "production" secret is ONLY available to jobs that
  reference environment: production — and only after approval is granted.

--- CREATING ENVIRONMENTS ---

Repo Settings → Environments → New environment

For staging:
  - No protection rules (deployments happen automatically)
  - Secrets: STAGING_DATABASE_URL, STAGING_API_KEY

For production:
  - Required reviewers: add 1-2 people who must approve
  - Wait timer: 5 minutes (lets you abort if you notice something wrong)
  - Allowed branches: only "main" (can't deploy from a feature branch)
  - Secrets: PRODUCTION_DATABASE_URL, PRODUCTION_API_KEY

--- EXAMPLE DEPLOY WORKFLOW ---

    name: Deploy
    on:
      workflow_dispatch:
        inputs:
          target:
            description: "Deploy target"
            type: environment    # dropdown populated from repo environments
            required: true

    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - run: pytest

      deploy-staging:
        needs: test
        runs-on: ubuntu-latest
        environment: staging     # unlocks staging secrets, logs deployment
        if: inputs.target == 'staging' || inputs.target == 'production'
        steps:
          - name: Deploy to staging
            run: |
              echo "Deploying to staging..."
              # ssh staging "docker pull image:$SHA && docker restart app"
            env:
              DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}

      deploy-production:
        needs: deploy-staging    # must deploy to staging before production
        runs-on: ubuntu-latest
        environment: production  # triggers approval gate (if configured)
        if: inputs.target == 'production'
        steps:
          - name: Deploy to production
            run: |
              echo "Deploying to production..."
            env:
              DATABASE_URL: ${{ secrets.PRODUCTION_DATABASE_URL }}

--- HOW THE APPROVAL GATE WORKS ---

When a job references environment: production (with required reviewers set):
  1. The job is queued but PAUSED — runner not allocated yet
  2. GitHub sends an email/notification to the required reviewers
  3. Reviewer goes to the Actions run page and clicks "Approve"
  4. GitHub allocates a runner and the job starts

If nobody approves within the timeout period (configurable, default: 30 days),
the deployment is auto-rejected.

This is the critical difference from a plain secrets approach:
  - Without environments: the job starts immediately, production secrets available
  - With environments: human eyes on "we're about to deploy to production"

--- SECRETS vs VARIABLES ---

Secrets (${{ secrets.NAME }}):
  - Encrypted at rest and in transit
  - Masked in logs (*** appears instead of the value)
  - Use for: API keys, database passwords, signing certificates, tokens
  - Cannot be read back via the UI after creation
  - Max 64KB per secret, max 100 per environment

Variables (${{ vars.NAME }}):
  - Stored in plaintext
  - Visible in the UI and in logs (not masked)
  - Use for: non-sensitive config — base URLs, feature flag names,
    deployment region names, version constraints
  - Can be updated and read back via the UI

Repository-level vs environment-level:
  Repository secrets: available to all jobs in all workflows
  Environment secrets: only available to jobs that reference that environment

    env:
      DB_URL: ${{ secrets.DATABASE_URL }}        # repo-level
      DB_URL: ${{ secrets.DATABASE_URL }}        # environment-level (same syntax,
                                                 # but only unlocked if environment: set)

--- MULTI-ENVIRONMENT PROMOTION PATTERN ---

The principle: build ONCE, deploy the same artifact to each environment.
Never rebuild between staging and production. The artifact that passed
staging tests is exactly what goes to production.

    build:
      outputs:
        image_digest: ${{ steps.build.outputs.digest }}

    deploy-staging:
      needs: build
      environment: staging
      steps:
        - run: deploy.sh ${{ needs.build.outputs.image_digest }} staging

    deploy-production:
      needs: [build, deploy-staging]
      environment: production
      steps:
        - run: deploy.sh ${{ needs.build.outputs.image_digest }} production

Note: outputs pass data between jobs. The digest is the immutable image reference —
not a mutable tag like "latest".

--- JOB DEPENDENCIES (needs:) ---

    jobs:
      test:         runs first
      build:
        needs: test     runs after test passes
      deploy-staging:
        needs: build    runs after build passes
      deploy-production:
        needs: [build, deploy-staging]  runs after BOTH pass

Without needs:, all jobs run in parallel.
With needs:, jobs form a directed acyclic graph (DAG).

--- EXERCISES ---

1. Create staging and production environments:
   Repo Settings → Environments.
   Add staging (no protection).
   Add production (required reviewer: yourself, wait timer: 1 minute).

2. Add environment secrets:
   In staging: add DEPLOY_TARGET=staging-server
   In production: add DEPLOY_TARGET=prod-server

3. Write a workflow that deploys to the selected environment:
   Use the example workflow above.
   Run it targeting staging — it should auto-proceed.
   Run it targeting production — it should pause waiting for your approval.

4. Observe the deployment log:
   After a successful deploy job, go to the repo homepage.
   A "staging" section appears under "Environments" on the right sidebar.
   Click it to see deployment history with links to the runs.

5. Test branch restriction:
   Add an allowed branch rule to production (only "main").
   Try triggering a production deploy from a feature branch.
   It should be blocked.
"""

ENVIRONMENT_CONCEPTS = {
    "environment: staging":    "Unlocks staging secrets, logs deployment, applies staging rules",
    "environment: production": "Same but with approval gate — job pauses for human review",
    "needs: [a, b]":           "This job runs only after both a and b succeed",
    "secrets.NAME":            "Encrypted; masked in logs — use for credentials",
    "vars.NAME":               "Plaintext config — use for non-sensitive settings",
    "outputs":                 "Pass data (e.g. image digest) from one job to another",
}

PROTECTION_RULE_OPTIONS = {
    "Required reviewers":     "1-6 people or teams who must approve before the job runs",
    "Wait timer":             "Delay (minutes) before the job starts — lets you abort",
    "Allowed branches":       "Only deploys triggered from matching branches run",
    "Prevent self-review":    "The person who triggered the workflow cannot approve it",
}
