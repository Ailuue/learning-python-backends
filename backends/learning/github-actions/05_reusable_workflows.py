"""
Reusable Workflows
==================

CONCEPTS:
  1. The problem: copy-pasting CI jobs across multiple repos/workflows
  2. workflow_call — the trigger that makes a workflow reusable
  3. Inputs and outputs — the interface contract
  4. Secrets: inherit vs explicit passing
  5. Calling a reusable workflow from another workflow
  6. Limitations of reusable workflows
  7. Composite Actions — the alternative for step-level reuse

--- THE PROBLEM ---

You have three services: api, worker, cron-job.
Each has a workflow that:
  1. Checks out code
  2. Sets up Python
  3. Caches pip
  4. Installs dependencies
  5. Runs pytest

You copy-paste the jobs. Six months later, you decide to add coverage
reporting. You update it in api's workflow, forget worker and cron-job.

Reusable workflows solve this: define the job pattern once,
call it from each service's workflow.

--- workflow_call TRIGGER ---

A workflow becomes reusable by adding `workflow_call` to its on: triggers.

    # .github/workflows/reusable-test.yml
    name: Reusable — Run Python Tests

    on:
      workflow_call:
        inputs:
          working_directory:
            description: "Path to the directory containing requirements.txt and pytest.ini"
            type: string
            required: true
          python_version:
            description: "Python version to test against"
            type: string
            default: "3.13"
        outputs:
          test_outcome:
            description: "passed or failed"
            value: ${{ jobs.test.outputs.outcome }}
        secrets:
          CODECOV_TOKEN:
            required: false

    jobs:
      test:
        runs-on: ubuntu-latest
        outputs:
          outcome: ${{ steps.run_tests.outcome }}
        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-python@v5
            with:
              python-version: ${{ inputs.python_version }}

          - uses: actions/cache@v4
            with:
              path: ~/.cache/pip
              key: ${{ runner.os }}-pip-${{ hashFiles(format('{0}/requirements.txt', inputs.working_directory)) }}

          - run: pip install -r requirements.txt
            working-directory: ${{ inputs.working_directory }}

          - name: Run tests
            id: run_tests
            run: pytest
            working-directory: ${{ inputs.working_directory }}

--- CALLING A REUSABLE WORKFLOW ---

    # .github/workflows/ci.yml  (caller)
    jobs:
      test-testing-concepts:
        uses: ./.github/workflows/reusable-test.yml   # local file
        with:
          working_directory: backends/learning/testing-concepts
          python_version: "3.13"

      test-bookmark-manager:
        uses: ./.github/workflows/reusable-test.yml
        with:
          working_directory: backends/bookmark_manager

Call a workflow from another repo:
      uses: my-org/shared-workflows/.github/workflows/python-test.yml@main
      with:
        python_version: "3.13"

Key rules:
  - uses: value must be a FULL path (repo/path@ref or ./local-path)
  - A job that uses: cannot have steps: — the whole job is delegated
  - The calling workflow's jobs can still use needs: to sequence them

--- SECRETS PASSING ---

Option A: secrets: inherit
    jobs:
      call-reusable:
        uses: ./.github/workflows/reusable-test.yml
        secrets: inherit    # ALL caller secrets forwarded to the callee

Option B: explicit forwarding
    jobs:
      call-reusable:
        uses: ./.github/workflows/reusable-test.yml
        secrets:
          CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}

secrets: inherit is convenient but passes everything — less auditable.
Explicit forwarding is the principle of least privilege: only what the
callee actually declares in its `secrets:` block is forwarded.

--- OUTPUTS FROM REUSABLE WORKFLOWS ---

The callee declares outputs at the workflow level:

    on:
      workflow_call:
        outputs:
          image_digest:
            value: ${{ jobs.build.outputs.digest }}

The caller reads them via needs:

    jobs:
      build:
        uses: ./.github/workflows/reusable-build.yml
      deploy:
        needs: build
        steps:
          - run: deploy.sh ${{ needs.build.outputs.image_digest }}

--- LIMITATIONS ---

1. Cannot call a reusable workflow from a composite action.
2. Cannot nest reusable workflows more than 4 levels deep.
3. Environment secrets are NOT inherited — they come from the callee's own environment.
4. A job using uses: cannot also have services: or container:.
5. Matrix is supported in the caller, not in the callee:
   BAD:  the reusable workflow itself cannot be a matrix — the caller handles that.

--- COMPOSITE ACTIONS vs REUSABLE WORKFLOWS ---

Composite Action (.github/actions/my-action/action.yml):
  - Reuses at the STEP level (not job level)
  - Defined in an action.yml file, not a workflow file
  - Can be used inside any job's steps block
  - Great for 3-5 step sequences you repeat across many jobs

Reusable Workflow:
  - Reuses an entire JOB (or set of jobs)
  - Runs on its own runner with its own checkout
  - Better for complete job patterns (setup + test + report)
  - Supports environments, secrets:inherit, and outputs

Choose composite actions for small step sequences.
Choose reusable workflows for complete job patterns.

--- EXAMPLE: COMPOSITE ACTION ---

    # .github/actions/setup-python-env/action.yml
    name: "Setup Python Environment"
    description: "Checkout, setup Python, cache pip, install deps"
    inputs:
      python-version:
        default: "3.13"
      working-directory:
        required: true

    runs:
      using: composite
      steps:
        - uses: actions/checkout@v4
        - uses: actions/setup-python@v5
          with:
            python-version: ${{ inputs.python-version }}
        - uses: actions/cache@v4
          with:
            path: ~/.cache/pip
            key: pip-${{ inputs.python-version }}-${{ hashFiles(format('{0}/requirements.txt', inputs.working-directory)) }}
        - run: pip install -r requirements.txt
          working-directory: ${{ inputs.working-directory }}
          shell: bash

Use it in any workflow:
    steps:
      - uses: ./.github/actions/setup-python-env
        with:
          working-directory: backends/learning/testing-concepts
      - run: pytest
        working-directory: backends/learning/testing-concepts

--- EXERCISES ---

1. Create the reusable-test.yml file:
   Copy the reusable workflow example above into .github/workflows/reusable-test.yml.
   Refactor ci.yml to use it instead of inline steps.

2. Call the reusable workflow from two different jobs:
   Add a second call for the bookmark_manager tests.
   Both should run in parallel since they have no needs: dependency.

3. Add a matrix to the caller:
   Instead of a fixed python_version, use a matrix in the calling job:
     strategy:
       matrix:
         python-version: ["3.11", "3.13"]
     uses: ./.github/workflows/reusable-test.yml
     with:
       python_version: ${{ matrix.python-version }}

4. Create a composite action for Python setup:
   Create .github/actions/setup-python-env/action.yml using the example above.
   Replace the setup steps in ci.yml with this action.
   Compare the workflow YAML before and after — how many lines did you save?

5. Add an output from the reusable workflow:
   Have the test job output the total number of tests run:
     - run: echo "count=$(pytest --co -q | wc -l)" >> $GITHUB_OUTPUT
       id: count
   Declare it as a workflow output and read it from the caller.
"""

REUSE_COMPARISON = {
    "Composite Action": "Step-level reuse — used inside a job's steps block",
    "Reusable Workflow": "Job-level reuse — the entire job is delegated",
}

WHEN_TO_USE = {
    "Composite Action":   "3-5 step sequences repeated in many jobs (setup, lint, etc.)",
    "Reusable Workflow":  "Full job patterns: checkout + test + report, or build + push",
    "Neither":            "One-off logic in a single workflow — don't over-abstract",
}

KEY_YAML_FIELDS = {
    "on: workflow_call":       "Makes this workflow callable by other workflows",
    "inputs:":                 "Parameters the caller must/can provide",
    "outputs:":                "Values the caller can read after the job runs",
    "secrets:":                "Secrets the callee needs (caller provides them)",
    "uses: ./path@ref":        "How to call a reusable workflow from a job",
    "secrets: inherit":        "Forward all caller secrets to the callee",
}
