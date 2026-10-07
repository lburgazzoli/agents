# gh pull request recipes

Read-only recipes for questions that need several fields in one call or hide a trap. One-liners live in the dispatch table in `SKILL.md`.

- `<n>` is a PR number, URL, or branch name. Omit it to target the PR of the current branch.
- Add `-R OWNER/REPO` when not in the repo's checkout.
- `gh api` paths fill `{owner}` and `{repo}` from the cwd remotes; write them literally outside the checkout.

## What is the state of the open PRs in this repo?

```bash
gh pr list -L 50 --json number,title,author,isDraft,reviewDecision,mergeable,updatedAt,statusCheckRollup --jq '
  def result: (.conclusion // .state);
  .[]
  | (.statusCheckRollup | {
      failed:  (map(select(result | IN("FAILURE","ERROR","TIMED_OUT","CANCELLED","ACTION_REQUIRED","STARTUP_FAILURE"))) | length),
      running: (map(select(.state == "PENDING" or (.status != null and .status != "COMPLETED"))) | length),
      total:   length}) as $c
  | [.number, .author.login,
     (if .isDraft then "DRAFT" elif .reviewDecision == "" then "-" else .reviewDecision end),
     .mergeable,
     (if $c.total == 0 then "no-checks" elif $c.failed > 0 then "\($c.failed)/\($c.total) failed" elif $c.running > 0 then "\($c.running)/\($c.total) running" else "passing" end),
     .updatedAt[0:10], .title]
  | @tsv'
```

Returns one row per open PR — number, author, review state, mergeable, checks, last update, title. Empty output means no open PRs. This one call replaces looping `gh pr view` over the list.

- `-L 50` is a cap, not a total: a result of exactly 50 rows may be truncated.
- `statusCheckRollup` makes the query slow (about 8 seconds for 50 PRs) and a larger `-L` can fail with `HTTP 504`. For a repo with more open PRs, run it twice with `-L 40 --search "sort:created-desc"` and `-L 40 --search "sort:created-asc"`, and widen from there. Drop the field and the checks column when only review state is needed.
- `mergeable` is often `UNKNOWN` in a list. Confirm with the merge-readiness recipe below before reporting a PR as blocked.
- App authors appear as `app/dependabot`.
- Narrow the scope with `--author @me`, `--search "review-requested:@me"`, `--draft=false`, or `--base <branch>`.

When reporting, do not echo the table. Group the PRs by what needs attention and give a count for each group: ready to merge (`APPROVED`, `MERGEABLE`, `passing`), failing checks, `CONFLICTING`, waiting for review, drafts. Call out PRs that have not been updated for weeks. Use the recipes below only for the PRs the user wants to drill into.

## Which PR belongs to the current branch?

```bash
gh pr view --json number,url,state,isDraft
```

Returns one object. A non-zero exit with `no pull requests found for branch` means there is none — use the exit code, do not parse the message.

For a branch that is not checked out:

```bash
gh pr list --head <branch> --state all --json number,state,url,headRepositoryOwner \
  --jq '.[] | [.number, .state, .headRepositoryOwner.login, .url] | @tsv'
```

`--state all` is needed because the default lists open PRs only. `--head` matches the branch name in any fork, so check the owner column when several rows come back.

## Can it merge, and what blocks it?

```bash
gh pr view <n> --json state,isDraft,mergeable,mergeStateStatus,reviewDecision,baseRefName,headRefOid
```

Returns one object. Read it as:

| Field | Values that matter |
|-------|--------------------|
| `mergeable` | `MERGEABLE`, `CONFLICTING` (rebase needed), `UNKNOWN` |
| `mergeStateStatus` | `CLEAN` ready · `BLOCKED` required review or check missing · `BEHIND` base moved · `DIRTY` conflicts · `UNSTABLE` non-required check failing · `DRAFT` |
| `reviewDecision` | `APPROVED`, `CHANGES_REQUESTED`, `REVIEW_REQUIRED`, empty when no review is required |

`UNKNOWN` means GitHub has not computed mergeability yet, not that the PR is broken. Run the same command again after a few seconds.

## Which checks are failing?

```bash
gh pr view <n> --json statusCheckRollup --jq '
  .statusCheckRollup[]
  | select((.conclusion // .state) | IN("FAILURE","ERROR","TIMED_OUT","CANCELLED","ACTION_REQUIRED","STARTUP_FAILURE"))
  | [(.name // .context), (.conclusion // .state), (.detailsUrl // .targetUrl)] | @tsv'
```

Returns one `name<TAB>result<TAB>url` row per failing check. Empty output means nothing has failed, not that everything passed: checks still running are excluded.

`statusCheckRollup` mixes two shapes. Check runs (GitHub Actions, Konflux) use `name`, `conclusion`, `detailsUrl`; commit statuses (Prow) use `context`, `state`, `targetUrl`. Filtering on `.conclusion` alone silently drops every Prow job.

To see what is still running, swap the `select` for:

```
select(.state == "PENDING" or (.status != null and .status != "COMPLETED"))
```

## What does it change?

```bash
gh pr view <n> --json additions,deletions,changedFiles,files \
  --jq '{additions, deletions, changedFiles, listed: (.files | length), paths: [.files[].path]}'
```

Returns the size and the changed paths without the diff. `files` stops at 100 entries: when `listed` is lower than `changedFiles`, get the full list with `gh pr diff <n> --name-only`.

## What has been said so far?

```bash
gh pr view <n> --json comments,latestReviews --jq '
  (.comments[] | ["comment", .author.login, .createdAt, .body]),
  (.latestReviews[] | ["review:" + .state, .author.login, .submittedAt, .body])
  | @tsv'
```

Returns one row per conversation comment, then one per reviewer with their latest verdict. Inline comments on the diff are not included — see the next recipe and "PR comments: two different things" in [read.md](../read.md).

Bot comments are often the bulk of the output. Bot logins appear here without the `[bot]` suffix, so drop them by bare name:

```
.comments[] | select(.author.login | IN("openshift-ci","codecov","coderabbitai") | not)
```

## Which review threads are unresolved?

```bash
gh api graphql \
  -f query='query($o:String!,$r:String!,$n:Int!){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100){totalCount nodes{isResolved path line comments(first:1){totalCount nodes{author{login} url body}}}}}}}' \
  -f o=OWNER -f r=REPO -F n=<n> \
  --jq '.data.repository.pullRequest.reviewThreads
    | (.nodes[] | select(.isResolved | not)
        | [.path, (.line // "outdated"), .comments.nodes[0].author.login, .comments.totalCount, .comments.nodes[0].url, .comments.nodes[0].body] | @tsv),
      "unresolved \([.nodes[] | select(.isResolved | not)] | length) of \(.totalCount) threads"'
```

Returns one row per unresolved thread — path, line, who opened it, number of comments, link, opening comment — then a summary line. Here `<n>` must be the number, and `-F` (not `-f`) passes it as an integer.

Resolution state exists only in GraphQL; the REST `pulls/<n>/comments` endpoint cannot tell resolved from unresolved. This is a `query`, so it stays within the `gh api` read-only rule. Only the first 100 threads are fetched: if the summary total is above 100, page with `after:`.

## Who has to act next?

```bash
gh pr view <n> --json author,isDraft,reviewDecision,reviewRequests,latestReviews --jq '
  {author: .author.login, isDraft, reviewDecision,
   requested: [.reviewRequests[] | (.login // .slug // .name)],
   reviews: [.latestReviews[] | {author: .author.login, state}]}'
```

Returns the author, the reviewers still being waited on, and each reviewer's latest verdict. A `CHANGES_REQUESTED` review or unresolved threads put the ball with the author; a non-empty `requested` list puts it with those reviewers.

A reviewer leaves `requested` as soon as they submit any review, so an empty list does not mean approved. Requested teams show up as a slug, not a login.

## Which issues does it close?

```bash
gh pr view <n> --json closingIssuesReferences \
  --jq '.closingIssuesReferences[] | [.number, .repository.owner.login + "/" + .repository.name, .url] | @tsv'
```

Returns one row per issue that merging will close, including issues in other repos. It covers closing keywords in the body and manually linked issues; a bare `#123` mention is not a closing reference and is not listed.

## Which PR introduced a commit?

```bash
gh api repos/{owner}/{repo}/commits/<sha>/pulls \
  --jq '.[] | [.number, .state, .merged_at, .html_url, .title] | @tsv'
```

Returns the PRs that contain the commit. This works for merge, squash, and rebase commits on the default branch, where searching PR titles for the SHA does not. `state` is `closed` for merged PRs; a non-empty `merged_at` is what says it merged.
