---
name: dev-gh
description: >
  GitHub CLI (gh) usage: token-efficient read patterns and a mandatory
  confirmation gate for every write. Triggers when running any gh command,
  or when reading or changing GitHub pull requests, issues, discussions,
  releases, workflow runs, checks, review comments, labels, or repo contents:
  "list PRs", "PR summary", "open PRs overview", "show issue", "PR checks",
  "why did CI fail", "review comments", "search issues", "comment on the PR",
  "merge", "close the issue", "gh api".
  Not for local git history (use dev-git) or cloning repos (use dev-context).
---

# GitHub CLI (gh)

Read freely and efficiently. Never write without the user's confirmation.

## Write gate — mandatory

A **write** is any command that creates, updates, edits, merges, closes, reopens, labels, assigns, reviews, comments on, deletes, triggers, or reconfigures anything on GitHub. Writes are visible to other people, send notifications, and are often impossible to undo, so the user decides each one — not the agent.

Before running any write:

1. **Stop.** Do not run the command yet.
2. **Show** the user the exact command, the target (`OWNER/REPO`, number), and the full text of any body, title, or comment that will be posted.
3. **Ask** for confirmation and wait for an explicit yes.
4. **Run** exactly what was approved. If anything changes (target, text, flags), go back to step 2.

One confirmation covers one write. Approval does not carry over to the next command, the next PR, or a retry with different arguments.

### What counts as a write

| Area | Read (no confirmation) | Write (confirm first) |
|------|------------------------|-----------------------|
| `gh pr` | `list` `view` `diff` `checks` `status` | `create` `edit` `comment` `review` `merge` `close` `reopen` `ready` `lock` `unlock` `update-branch` `revert` |
| `gh issue` | `list` `view` `status` | `create` `edit` `comment` `close` `reopen` `delete` `transfer` `pin` `unpin` `lock` `unlock` `develop` |
| `gh discussion` | `list` `view` | `create` `edit` `comment` |
| `gh repo` | `view` `list` `read-file` `read-dir` | `create` `edit` `delete` `fork` `rename` `archive` `unarchive` `sync` `set-default` `deploy-key add/delete` |
| `gh release` | `list` `view` `download` | `create` `edit` `delete` `upload` `delete-asset` |
| `gh run` / `gh workflow` | `list` `view` `watch` `download` | `rerun` `cancel` `delete` / `run` `enable` `disable` |
| `gh label` | `list` | `create` `edit` `delete` `clone` |
| `gh secret` / `gh variable` | `list` `get` | `set` `delete` |
| `gh cache` / `gh ruleset` | `list` `view` `check` | `cache delete` |
| `gh gist` | `list` `view` | `create` `edit` `delete` `rename` `clone` |
| `gh project` | `list` `view` `item-list` `field-list` | everything else |
| `gh search` / `gh status` / `gh auth status` | always read | — |

A subcommand not listed here is a write until `gh <cmd> <sub> --help` shows it only reads. `gh auth login/logout/refresh/switch`, `gh config set`, `gh extension install`, and `gh alias set` change local state — confirm those too.

`gh pr checkout` and `gh issue develop --checkout` switch the local branch. To only read a PR, use `gh pr diff <n>` or `gh pr view <n>`.

### `gh api` is read-only

Never use `gh api` to change anything. Use the dedicated subcommand, which validates input and makes the intent reviewable.

- Never pass `--method`/`-X` with `POST`, `PUT`, `PATCH`, or `DELETE`.
- Never pass `-f`, `-F`, `--field`, `--raw-field`, or `--input` to a REST endpoint without `-X GET`. Supplying fields silently switches the request to `POST`.
- `gh api graphql` is allowed only for `query` operations. Never send a `mutation`.

If a write has no dedicated subcommand, **stop and report the limitation** to the user. Do not fall back to a mutating `gh api` call, even if the user already approved the write — approval covers the action, not that mechanism. Only an explicit instruction from the user to use `gh api` for that specific write lifts this, and the write gate still applies.

### No exceptions

| Excuse | Why it does not hold |
|--------|----------------------|
| "The user asked me to comment/merge, that is the confirmation" | The request names the goal. Confirmation is for the exact command and text, which the user has not seen yet. |
| "It is tiny — just a label / a reaction / a typo fix" | Size is not the test. It still notifies people and lands under the user's name. |
| "I got a yes a moment ago" | That yes was for that command. Ask again. |
| "It is reversible" | The notification, the CI run, and the audit entry are not. |
| "I am running autonomously, nobody is there to ask" | Then the write does not happen. Report the command you would have run and stop. |
| "No subcommand supports it, so `gh api -X POST` is the only way" | Then the answer is to report that, not to do it. |
| "`--dry-run` / `--web` makes it safe" | Not reliably: `gh pr create --dry-run` may still push the branch. Check `--help`, and confirm anyway. |

## Reading efficiently

One call should answer the question, with only the fields needed.

1. **Always `--json` + `--jq`** — default output is column text meant for humans. `--json field1,field2` selects fields; `--jq` filters in-process, no separate `jq` pipe.
2. **Discover fields, don't guess** — `--json` with no field list prints every available field.
3. **Set `-L`** — list and search commands silently stop at 30. Pass `-L N` and treat it as a cap, not a total.
4. **Emit `@tsv`** for tabular results; it is the most compact form.
5. **`-R OWNER/REPO`** when not in the repo's checkout. Otherwise gh infers the repo from the cwd remotes.
6. **No pager workarounds** — in a non-TTY gh already skips the pager, strips color, and fails fast instead of prompting. `--no-pager` does not exist.

### Intent dispatch

| Need | Command |
|------|---------|
| PRs/issues in one repo | `gh pr list -L 50 --json number,title,author --jq '.[] \| [.number,.author.login,.title] \| @tsv'` |
| Cross-repo, or filter by author/label/text | `gh search prs\|issues <qualifiers> -L 50 --json ...` |
| One PR/issue, specific fields | `gh pr view <n> --json title,body,state,reviewDecision,mergeable` |
| PR changes | `gh pr diff <n>` · file names only: `gh pr diff <n> --name-only` |
| Conversation comments | `gh pr view <n> --json comments --jq '.comments[] \| [.author.login,.body] \| @tsv'` |
| Inline review comments | `gh api --paginate repos/{owner}/{repo}/pulls/<n>/comments --jq '.[] \| [.user.login,.path,.line,.body] \| @tsv'` |
| CI state | `gh pr checks <n> --json name,bucket,link --jq '.[] \| select(.bucket!="pass")'` |
| Why CI failed | `gh run view <run-id> --log-failed` (never `--log`, it is unbounded) |
| Recent runs | `gh run list -L 10 --json databaseId,workflowName,conclusion,headBranch` |
| A file without cloning | `gh repo read-file <path> -R OWNER/REPO [--ref <ref>]` |
| A directory listing | `gh repo read-dir [<path>] -R OWNER/REPO [--ref <ref>]` |
| True total count | `gh api graphql -f query='query($o:String!,$r:String!){repository(owner:$o,name:$r){issues(states:OPEN){totalCount}}}' -f o=OWNER -f r=REPO --jq '.data.repository.issues.totalCount'` |
| Anything `--json` lacks | `gh api --paginate <path> --jq '...'` (add `--slurp` to merge pages into one array) |
| REST read with parameters | `gh api -X GET <path> -f state=closed -f per_page=50` (`-X GET` is required) |
| Who am I / which host | `gh auth status --json hosts` |

### Search vs list

- `gh search issues|prs|code|repos|commits|users` uses the search index. Pass each qualifier as its **own bare token**: `gh search issues repo:cli/cli is:open author:monalisa`. Quoting them together (`"repo:cli/cli is:open"`) is parsed as one keyword and fails with `Invalid search query`. Quote only multi-word free text.
- `gh pr list --search "..."` / `gh issue list --search "..."` take the query as **one quoted string** and are scoped to one repo.
- Bots author as GitHub Apps: `--author dependabot` matches nothing. Use `--app dependabot` or `--author "dependabot[bot]"`.
- `gh search issues --search-type semantic|hybrid` (github.com/GHEC, issues only) when the user describes a problem rather than exact terms.

### Anti-patterns

| Instead of | Do this |
|------------|---------|
| `gh pr view <n>` and reading the text | `gh pr view <n> --json <fields> --jq ...` |
| `gh pr list \| grep ...` | `--search`, `--author`, `--label`, or `--jq 'select(...)'` |
| Looping `gh pr view` over a list | One `gh pr list --json ...` with every field needed |
| Cloning a repo to read one file | `gh repo read-file` |
| `gh run view --log` | `gh run view --log-failed`, or `--job <id>` |
| `gh api` for something a typed command returns | The typed command with `--json` |
| `gh api <path> -f key=value` to filter a read | `gh api -X GET <path> -f key=value` |
| Trusting a 30-row result as complete | Set `-L`, or query `totalCount` |
| `gh pr checkout` just to look at a PR | `gh pr diff <n>` |

## References

Read on demand:

- [references/read.md](references/read.md) — JSON field shapes for issue types, sub-issues and relationships; discussions; `read-file`/`read-dir` details; templates; environment variables.
- [references/write.md](references/write.md) — flags for the write commands (issue types and relationships, attachments, discussions, worktree checkouts). Read only after the user has asked for a write; the write gate still applies to every command in it.

Recipes — verified read commands for questions that need several fields at once or hide a trap. One file per kind:

| File | Read when |
|------|-----------|
| [references/recipes/pr.md](references/recipes/pr.md) | Summary of the repo's open PRs; finding the PR for a branch or commit; merge readiness and blockers; failing or pending checks (Actions and Prow); change size; unresolved review threads; who has to act next; linked issues |
