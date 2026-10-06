# gh write reference

Every command in this file is a write. The write gate in `SKILL.md` applies to each one: show the exact command and the full text to be posted, ask, wait for an explicit yes, then run exactly what was approved.

Derived from the upstream [`gh` skill](https://github.com/cli/cli/blob/trunk/skills/gh/SKILL.md).

## Before proposing a write

- Read the current state first (`gh pr view`, `gh issue view --json ...`) so the proposal is accurate.
- In a non-TTY gh does not prompt; it errors when required flags are missing (e.g. `must provide --title and --body when not running interactively`). Supply every required flag in the command shown to the user.
- Put long bodies in a file and pass `--body-file <path>`; show the user the file content.
- `gh pr create --dry-run` prints the PR details instead of creating it, but may still push the branch — it is still a write, so confirm first. Check `--help` before relying on `--dry-run` on any other command.

## Issue types, sub-issues, relationships

- `gh issue create`: `--type <name>`, `--parent <number|url>` (creates it as a sub-issue), `--blocked-by <number|url,...>`, `--blocking <number|url,...>`.
- `gh issue edit` (one or more issues in the same repo, e.g. `gh issue edit 23 34`):
  - `--type <name>` / `--remove-type`
  - `--parent <n|url>` / `--remove-parent`
  - `--add-sub-issue <n,n>` / `--remove-sub-issue <n,n>`
  - `--add-blocked-by <n,n>` / `--remove-blocked-by <n,n>`
  - `--add-blocking <n,n>` / `--remove-blocking <n,n>`
- References are issue numbers or URLs. A URL may point to another repo on the same host; a different host is rejected.
- `--add-sub-issue` cannot be used when editing more than one issue.
- GHES: issue types and sub-issues need 3.17+; relationships need 3.19+.

## Attachments

`--attach <path>` exists on `gh issue create|edit|comment` and `gh pr create|edit|comment`.

- Repeat the flag for multiple files; at most 50 per invocation.
- Supported: `png`, `jpg`, `jpeg`, `gif`, `webp`, `svg`, `mp4`, `mov`, `webm`.
- Image alt text goes after `#`, quoted so the shell keeps it: `--attach './login.png#The login error state'`. Without it the filename is used. Videos cannot take alt text.
- If the body references the attached path, gh rewrites that Markdown reference to the uploaded URL; otherwise it appends the attachment to the body.
- A reference-style video image (`![rec][clip]` with `[clip]: ./repro.mp4`) is rejected; use a reference-style link.
- Not combinable with `--web`; on `gh pr create` also not with `--dry-run`; on `gh issue edit` only one issue at a time; on `comment` not with `--delete-last`.
- Needs GitHub.com or a GHE.com tenant, a user token (OAuth, classic or fine-grained PAT), and write access. GHES and most GitHub App tokens are unsupported.
- Uploads stop at the first failure, but files already uploaded are still written and gh exits non-zero — re-read the issue/PR before retrying.

## Discussions (preview)

- `gh discussion create --title <t> (--body <b> | --body-file <path>) --category <name> [--label <name>,...]` — title, body and category are required non-interactively.
- `gh discussion edit {<number>|<url>} [--title] [--body|--body-file] [--category] [--add-label] [--remove-label]`
- `gh discussion comment {<number>|<discussion-url>|<comment-id>|<comment-url>} [--body|--body-file] [--edit] [--delete] [--yes]`
  - A discussion argument adds a top-level comment; a comment argument adds a reply.
  - `--edit` / `--delete` need a comment ID or URL. `--yes` skips gh's own delete prompt — it does not replace the user's confirmation.
- `create` and `edit` print the discussion URL; `comment` prints the comment URL. No `--json` on these.

## Local checkouts

These change the local working tree, and `develop` also creates a branch on GitHub.

- `gh pr checkout <n>` switches the current branch. `--worktree <path>` checks out into a git worktree instead.
- `gh issue develop <n> --checkout` creates a linked branch and checks it out. `--worktree <path>` requires `--checkout`, cannot be blank, and cannot be combined with `--list`.

## No dedicated subcommand

If the write the user wants has no `gh` subcommand (for example resolving a review thread or adding a reaction), stop and tell the user which operation is unsupported, and offer the web URL (`gh pr view <n> --json url --jq .url`) so they can do it themselves. Keep `gh api` read-only: no `POST`/`PUT`/`PATCH`/`DELETE`, no `-f`/`-F` on a REST endpoint without `-X GET`, no GraphQL `mutation`.
