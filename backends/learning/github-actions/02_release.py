"""
Release Workflow — .github/workflows/release.yml
==================================================

CONCEPTS:
  1. Semantic versioning — what v1.2.3 means
  2. Git tags — lightweight vs annotated
  3. Why tests run before publishing a release
  4. Auto-generated release notes from PRs and commits
  5. The GITHUB_TOKEN permission model
  6. What a GitHub Release is (vs a tag)

--- SEMANTIC VERSIONING ---

v MAJOR . MINOR . PATCH

  MAJOR: breaking change — callers must update their code
  MINOR: new feature, backwards compatible
  PATCH: bug fix, backwards compatible

v0.x.x: pre-1.0, no stability guarantee
v1.0.0: first stable release
v2.0.0: breaking change from v1.x.x

For an internal API or monorepo (like this learning repo), versioning
marks a stable checkpoint — a commit you'd want to reference by name
instead of by SHA.

--- GIT TAGS ---

Lightweight tag (pointer to a commit):
  git tag v1.2.3
  git push origin v1.2.3

Annotated tag (tag object with its own metadata, recommended):
  git tag -a v1.2.3 -m "Release v1.2.3: add testing-concepts module"
  git push origin v1.2.3

Push all tags at once (use sparingly — pushes ALL local tags):
  git push origin --tags

Delete a tag (if you tagged the wrong commit):
  git tag -d v1.2.3          # local
  git push origin :v1.2.3    # remote

--- TRIGGER ---

    on:
      push:
        tags:
          - "v*.*.*"

Matches any tag that starts with "v" and has the semver structure.
v1.0.0, v0.2.1, v10.0.0-rc.1 — all trigger this workflow.
A push of a branch named "v1.0.0" does NOT trigger it (tags and branches
are distinct refs).

--- WHY RUN TESTS BEFORE RELEASING ---

The release tag and GitHub Release should only exist if the code at that
commit actually passes. Otherwise you've tagged a broken commit and shipped
a release that doesn't work.

Pattern:
  1. Tests pass on main → CI is green
  2. Tag the commit: git tag v1.2.3 && git push origin v1.2.3
  3. release.yml triggers → re-runs tests (proves THIS exact commit is good)
  4. Only if tests pass → create the GitHub Release

This matters because main might have moved between CI passing and you tagging.
Running tests in release.yml is the final gate.

--- AUTO-GENERATED RELEASE NOTES ---

GitHub can generate release notes automatically from:
  - Pull requests merged since the previous tag
  - Commits since the previous tag (if no PRs)

    uses: softprops/action-gh-release@v2
    with:
      generate_release_notes: true

GitHub groups PRs by their labels:
  "bug"      → Bug Fixes section
  "feature"  → New Features section
  (unlabeled) → Other Changes section

Configure the categories in .github/release.yml:
  changelog:
    categories:
      - title: "🚀 Features"
        labels: [feature, enhancement]
      - title: "🐛 Bug Fixes"
        labels: [bug, fix]

Without labels, all PRs land in "Other Changes". Add labels to PRs to
get a structured changelog automatically.

--- PERMISSIONS ---

GitHub Actions jobs run with a GITHUB_TOKEN that is auto-provisioned per run.
By default it has read-only access to contents.

To create a release, the job needs write access:

    permissions:
      contents: write

This is the principle of least privilege: jobs only get the permissions
they explicitly declare. Don't use broader permissions than needed.

Alternatives to GITHUB_TOKEN:
  - Personal Access Token (PAT) stored as a repo secret — more permissions
    but a human's token, a security risk if the PAT has broad scope
  - GitHub App installation token — the modern approach for automation;
    granular permissions, auto-rotated, auditable

--- EXTRACTING THE VERSION NUMBER ---

    - name: Extract version
      id: version
      run: echo "VERSION=${GITHUB_REF_NAME#v}" >> "$GITHUB_OUTPUT"

GITHUB_REF_NAME is the tag name: "v1.2.3"
${GITHUB_REF_NAME#v} strips the leading "v": "1.2.3"
>> "$GITHUB_OUTPUT" writes a step output named VERSION.
Reference it later: ${{ steps.version.outputs.VERSION }}

This is useful when you need the bare version number for package names,
Docker image tags, or release body text.

--- GITHUB RELEASE vs GIT TAG ---

A git tag is just a pointer to a commit. It lives in the repo.

A GitHub Release is a GitHub UI concept built on top of a tag. It adds:
  - A title
  - A description (markdown body)
  - Attached binary artifacts (zip, wheels, compiled binaries)
  - A "Latest release" marker

Users see releases on the repo's /releases page.
The GitHub API exposes releases separately from tags.
Releases can be marked as "pre-release" (beta, rc) or "latest".

--- EXERCISES ---

1. Create and push a tag:
     git tag v0.1.0
     git push origin v0.1.0
   Watch release.yml trigger in the Actions tab.
   After it completes, check the repo's /releases page.

2. Draft release first, then publish:
   Change the workflow to create a draft release:
     uses: softprops/action-gh-release@v2
     with:
       draft: true
       generate_release_notes: true
   Review the draft before publishing. Useful for adding a hand-written
   summary on top of the auto-generated notes.

3. Add a pre-release:
   Tag with a pre-release suffix: git tag v1.0.0-rc.1
   Add to the workflow:
     prerelease: ${{ contains(github.ref_name, '-') }}
   Tags with a hyphen (rc, beta, alpha) are auto-marked as pre-release.

4. Attach a build artifact to the release:
   After running tests, zip the testing-concepts folder and attach it:
     - run: zip -r testing-concepts.zip backends/learning/testing-concepts/
     - uses: softprops/action-gh-release@v2
       with:
         files: testing-concepts.zip

5. Configure release categories:
   Create .github/release.yml with category config (see above).
   Label some PRs with "feature" or "bug", merge them, tag a release,
   and observe the structured changelog.
"""

SEMVER_RULES = {
    "MAJOR": "Breaking API change — consumers must update",
    "MINOR": "New backwards-compatible feature",
    "PATCH": "Backwards-compatible bug fix",
    "pre-release": "v1.0.0-rc.1, v2.0.0-beta.3 — not stable",
}

TAG_COMMANDS = {
    "create_lightweight": "git tag v1.2.3",
    "create_annotated":   "git tag -a v1.2.3 -m 'Release message'",
    "push_single":        "git push origin v1.2.3",
    "push_all":           "git push origin --tags",
    "delete_local":       "git tag -d v1.2.3",
    "delete_remote":      "git push origin :v1.2.3",
    "list":               "git tag --list 'v*' --sort=-version:refname",
}
