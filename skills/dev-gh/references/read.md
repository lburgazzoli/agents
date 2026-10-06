# gh read reference

Details for read operations beyond the dispatch table in `SKILL.md`. Derived from the upstream [`gh` skill](https://github.com/cli/cli/blob/trunk/skills/gh/SKILL.md).

## Output shaping

- `--json f1,f2` selects fields; with no field list it prints the available ones.
- `--jq '<expr>'` filters in-process.
- `--template '<go-template>'` (with `--json`) shapes text output. `-T` collides with a body-template flag on `gh pr create` and `gh issue create` — check `--help` before using the short form.
- `gh pr list` / `gh issue list` do not expose `totalCount` through `--json`. Use a GraphQL `query` for a true total.
- `gh api --paginate <path>` follows every page; add `--slurp` to wrap the pages into a single array before `--jq` runs.
- In `gh api` paths, `{owner}` and `{repo}` are filled from the cwd remotes. Write them literally for determinism or when outside the checkout.

## Issue types, sub-issues, relationships

`gh issue view` and `gh issue list` accept these `--json` fields: `issueType`, `parent`, `subIssues`, `subIssuesSummary`, `blockedBy`, `blocking`.

- `subIssues`, `blockedBy`, `blocking` are objects shaped `{"nodes": [...], "totalCount": N}`, not flat arrays.
- `nodes` is capped (`subIssues` at 100, `blockedBy`/`blocking` at 50). Compare `nodes | length` with `totalCount` to detect truncation.
- `gh issue list --type <name>` filters by issue type.
- GHES: issue types and sub-issues need 3.17+; blocked-by/blocking need 3.19+.

```bash
gh issue view 123 --json subIssues \
  --jq '.subIssues | {shown: (.nodes | length), total: .totalCount, items: [.nodes[] | {number, title, state}]}'
```

## Discussions (preview)

- `gh discussion list [--state open|closed|all] [--category <name>] [--author <handle>] [--label <name>,...] [--answered] [--search <query>] [--sort created|updated] [--order asc|desc] [--limit N] [--after <cursor>] [--json <fields>]`
  - Defaults: `--state open`, `--sort updated`, `--order desc`.
  - `--answered` is tri-state: `--answered=false` lists unanswered Q&A discussions.
- `gh discussion view {<number>|<url>|<comment-id>|<comment-url>} [--comments] [--order oldest|newest] [--limit N] [--after <cursor>] [--json <fields>]`
  - `--comments` adds the discussion's comments.
  - Pass a comment ID or URL as the argument to list that comment's replies. There is no `--replies` flag, and `--comments` is rejected with a comment argument.
  - `--order` (default newest), `--limit`, `--after` apply only to comment and reply listings.

## Repo contents without cloning (preview)

Both honor `-R OWNER/REPO` and `--ref <branch|tag|commit>` (default branch when omitted).

- `gh repo read-file <path> [--ref <ref>] [--output <path> [--clobber]] [--allow-escape-sequences] [--json <fields>] [--jq <expr>]`
  - Non-TTY: raw bytes to stdout.
  - A file containing terminal escape sequences is refused unless `--allow-escape-sequences` is passed.
  - `-o <path>` writes to disk (trailing slash keeps the remote file name; `--clobber` allows overwrite). Mutually exclusive with `--json`.
  - `--json` fields: `name`, `path`, `gitSHA`, `size`, `type`, `encoding`, `content` (base64).
- `gh repo read-dir [<path>] [--ref <ref>] [--json <fields>] [--jq <expr>]`
  - No path lists the repo root. Non-TTY output is tab separated: type, name, octal mode, byte size.
  - `--json` fields: `name`, `path`, `type`, `gitType`, `mode`, `modeOctal`, `gitSHA`, `size`, `submodule`.
  - A path that is a file errors and points at `read-file`, and vice versa.

## PR comments: two different things

- `gh pr view <n> --comments` / `--json comments` returns issue-level conversation comments only.
- Inline review comments on the diff come from `gh api --paginate repos/{owner}/{repo}/pulls/<n>/comments`.
- Review summaries and verdicts: `gh pr view <n> --json reviews,reviewDecision`.

## Environment

- `NO_COLOR`, `CLICOLOR_FORCE`, and `GH_FORCE_TTY` are honored. Leave `GH_FORCE_TTY` unset unless TTY-style output is specifically needed.
- `gh auth status` shows the active host, user, and which token env var is in effect; `--json` is supported.
