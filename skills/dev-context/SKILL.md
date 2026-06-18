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

- Cloned reference repositories and tooling dependencies live under `.context/repos/<org>/`. Skills such as `rhai-upgrade-assessment` must follow the cloning rules below.
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

### Rules

- **Always** clone to `.context/repos/<org>/<repo>@<branch>` — resolve the default branch name if none is specified. The `<org>` is the GitHub organization or user (e.g., `opendatahub-io`, `red-hat-data-services`, `kubeflow`).
- If the repository is already cloned, **do not** switch branches in place — refresh with `git -C <path> pull --ff-only`. Stale clones produce stale results.
- For another ref, use a separate clone at `.context/repos/<org>/<repo>@<ref>`.
- **Commit SHA** (after a clone that contains it): `git -C .context/repos/<org>/<repo>@<branch> fetch origin <sha> && git -C .context/repos/<org>/<repo>@<branch> checkout <sha>`

### Pull Request Checkout

When checking out a PR (e.g., `https://github.com/org/repo/pull/123` or `org/repo#123`), always clone the **head (source) fork and branch** — the branch the code is coming from, not the base branch it targets.

1. Resolve the PR's head ref using `gh pr view <number> --repo <org>/<repo> --json headRefName,headRepository,headRepositoryOwner`.
2. Clone from the head owner's fork at the head branch:

```bash
# Example: PR from lburgazzoli/foo@my-feature → org/foo@main
# Clone the SOURCE, not the target:
gh pr view 123 --repo org/foo --json headRefName,headRepository,headRepositoryOwner --jq '{owner: .headRepositoryOwner.login, repo: .headRepository.name, branch: .headRefName}'
# → {"owner":"lburgazzoli","repo":"foo","branch":"my-feature"}

git clone --depth 1 --single-branch --branch my-feature \
  https://github.com/lburgazzoli/foo \
  .context/repos/lburgazzoli/foo@my-feature
```

3. Follow the standard `<org>/<repo>@<branch>` directory convention — `<org>` is the **head owner** (fork owner), not the upstream org.

### Git worktree (optional, from the default clone after it exists): `git -C .context/repos/<org>/<repo> worktree add <path> <ref>` with `<path>` under `.context/repos/<org>/` (e.g. `opendatahub-io/odh-gitops-wt-rhoai-3.3` alongside the main repo). Use when you want one object database and multiple checkouts. **When the task is finished, remove the worktree** so `.context/` does not accumulate cruft: `git -C .context/repos/<org>/<repo> worktree remove <path>` (or `git worktree remove` from the worktree path), then `git -C .context/repos/<org>/<repo> worktree prune` if needed. Failed or abandoned runs should still be cleaned up.

