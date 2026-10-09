---
name: dev-context
description: >
  MANDATORY conventions for cloning any git repository or checking out any branch/tag/ref.
  Triggers on: "clone", "git clone", "checkout repository", "fetch repository", "pull repository",
  "clone this", "clone <url>", "get the source for", any GitHub URL intended for cloning,
  any task that needs a local copy of a remote repository, working with .context/repos/ paths,
  upgrade assessments, ad-hoc diffs across refs, or checking out a pull request / PR URL.
  ALL repository clones MUST go into .context/repos/ — never clone to the current directory,
  /tmp, or any other location.
user-invocable: false
---

# Context Directory and Repository Management

## Working Directory Conventions

- Cloned reference repositories and tooling dependencies live under `.context/repos/<org>/`. Any skill or task that needs a local copy of a repository must follow the cloning rules below.
- If a temporary file needs to be created, use `.context/`

## Repository Cloning and Refs

Use these rules for **any** task that clones, fetches, or checks out a repository — not just `.context/repos/` work. Goals: **fresh** default branches, **isolated** checkouts for specific refs, no hidden branch switches on the shared default clone.

### Cloning

Target directory is always `.context/repos/<org>/<repo>@<branch>`.

Given a URL like `https://github.com/kubeflow/model-registry` or `kubeflow/model-registry`:
- `<org>` = `kubeflow`
- `<repo>` = `model-registry`
- Clone to: `.context/repos/kubeflow/model-registry@main` (resolve the default branch name)

```bash
# Example: clone kubeflow/model-registry
git clone --depth 1 --single-branch https://github.com/kubeflow/model-registry .context/repos/kubeflow/model-registry@main

# Example: clone a specific branch
git clone --depth 1 --single-branch --branch v0.2.0 https://github.com/kubeflow/model-registry .context/repos/kubeflow/model-registry@v0.2.0
```

The bundled [clone.sh](scripts/clone.sh) applies this layout in one step: it resolves the default branch when none is given, clones shallow, fast-forwards an existing clone, and prints the clone path. The path is relative to this skill's directory.

```bash
scripts/clone.sh --repo kubeflow/model-registry                    # default branch
scripts/clone.sh --repo kubeflow/model-registry --branch v0.2.0    # specific branch/tag
scripts/clone.sh --repo https://github.com/kubeflow/model-registry # full URL
scripts/clone.sh --pr https://github.com/kubeflow/model-registry/pull/123  # pull request
```

### Rules

- **Always** clone to `.context/repos/<org>/<repo>@<branch>` — resolve the default branch name if none is specified. The `<org>` is the GitHub organization or user (e.g., `opendatahub-io`, `red-hat-data-services`, `kubeflow`).
- If the repository is already cloned, **do not** switch branches in place — refresh with `git -C <path> pull --ff-only`. Stale clones produce stale results.
- For another ref, use a separate clone at `.context/repos/<org>/<repo>@<ref>`.
- A `/` in the ref becomes `-` in the directory name (`feature/x` → `<repo>@feature-x`), so a ref never creates a nested directory.
- **Commit SHA** (after a clone that contains it): `git -C .context/repos/<org>/<repo>@<branch> fetch origin <sha> && git -C .context/repos/<org>/<repo>@<branch> checkout <sha>`

### Pull Request Checkout

Check out a GitHub PR (e.g., `https://github.com/org/repo/pull/123` or `org/repo#123`) into `.context/repos/<org>/<repo>@pr-<number>`, where `<org>` is the **upstream** org the PR was opened against, not the fork owner.

```bash
scripts/clone.sh --pr https://github.com/org/foo/pull/123   # PR URL
scripts/clone.sh --pr org/foo#123                           # short form
scripts/clone.sh --repo org/foo --pr 123                    # repo + number
# → .context/repos/org/foo@pr-123
```

The script fetches `refs/pull/<number>/head` from the upstream repository, so it needs no `gh` and still works when the head fork or branch has been deleted (merged or closed PRs). Run it again to refresh the clone to the PR's current head; a force-pushed PR is handled, and local modifications in the clone are never overwritten.

Equivalent git commands when the script cannot be used:

```bash
git init -q .context/repos/org/foo@pr-123
git -C .context/repos/org/foo@pr-123 remote add origin https://github.com/org/foo.git
git -C .context/repos/org/foo@pr-123 fetch --depth 1 origin "+refs/pull/123/head:refs/remotes/origin/pr-123"
git -C .context/repos/org/foo@pr-123 checkout -B pr-123 refs/remotes/origin/pr-123
```

- `refs/pull/<number>/head` is GitHub-specific; other forges need their own ref (e.g., GitLab's `refs/merge-requests/<number>/head`).
- The checkout is depth 1 and has no merge base with the target branch. To see what the PR changes, read the PR diff from GitHub (`gh pr diff <number> --repo <org>/<repo>`) rather than diffing locally.
- The PR ref is read-only. Only when the task must **push to the PR's branch**, clone the head fork instead: resolve it with `gh pr view <number> --repo <org>/<repo> --json headRefName,headRepositoryOwner` and clone to `.context/repos/<head-owner>/<repo>@<head-branch>`.

### Git worktree (optional)

Use a worktree when you want one object database and multiple checkouts. Create it from the default clone after it exists, with `<path>` under `.context/repos/<org>/` (e.g. `opendatahub-io/odh-gitops-wt-rhoai-3.3` alongside the main repo):

```bash
git -C .context/repos/<org>/<repo>@<branch> worktree add <path> <ref>
```

**When the task is finished, remove the worktree** so `.context/` does not accumulate cruft. Failed or abandoned runs should still be cleaned up.

```bash
git -C .context/repos/<org>/<repo>@<branch> worktree remove <path>
git -C .context/repos/<org>/<repo>@<branch> worktree prune   # if needed
```
