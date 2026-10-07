---
name: dev-openshift-ci
description: >
  Retrieve and analyze OpenShift CI (Prow) job failures on a GitHub pull
  request. Triggers on: "openshift-ci failed", "why did the e2e job fail",
  "investigate the CI failure on PR #N", "ci/prow/..." checks, comments from
  openshift-ci[bot], prow.ci.openshift.org links, test-platform-results
  gs:// paths, ci-operator, must-gather or gather-extra artifacts of a CI
  run. Not for GitHub Actions, Konflux, or other checks (use dev-gh).
---

# OpenShift CI failure analysis

Find the failed run, download only what explains it, and report the cause with evidence.

Requires `gh`, `jq`, `gcloud` (already authenticated) and `uv`. Everything goes through one entry point, `scripts/main.py <command>`, with the commands `runs`, `fetch`, `summary` and `junit`; the path is relative to this skill's directory. `scripts/main.py <command> --help` lists a command's flags.

## Workflow

### 1. Resolve the run

```bash
scripts/main.py runs 4137                                # PR of the repo you are in
scripts/main.py runs                                     # PR of the current branch
scripts/main.py runs owner/repo#4137                     # any repo, from anywhere
scripts/main.py runs <PR URL>
scripts/main.py runs <PR URL>#issuecomment-<id>          # the runs of that bot comment
scripts/main.py runs <Prow URL>
```

Output is TSV, newest first: `context  state  build_id  created_at  gs_url  prow_url`.

- **Pass what the user gave you.** For "PR #4137" with no repo, pass the number: the script reads the repo from the git checkout it runs in (the upstream repo when the checkout is a fork) and prints the resolved `owner/repo#n` on stderr. Do not ask which repo, and do not supply one from memory. Outside a git repository it fails and asks for `--repo` or a URL; relay that.
- **Only `openshift-ci[bot]` counts.** The script reads that bot's test report comment and its `ci/prow/*` statuses. Other bots, human comments (including `/retest` and `/test`), GitHub Actions and Konflux checks are not openshift-ci runs and are ignored.
- **Never build a `gs://` path by hand.** The job name and build ID change on every run; a path copied from an earlier run points at a different failure.

Without a comment URL, the script uses the latest test report comment, and only when that comment is for the PR's head commit.

**Exit code 2 means the script could not determine the run.** It prints the candidates: the report comments, and the `ci/prow` runs of the commit. Then:

1. Show the user that list (job, state, build ID, date).
2. Ask which run to analyze, and wait for the answer.
3. Rerun with the chosen comment URL or `--build <id>`.

Do not pick the most likely row yourself. A diagnosis of the wrong run is confident, detailed, and useless, and the user cannot tell from the report that it is about a run they did not mean.

`--list` prints the same candidates without choosing (exit 0); use it to compare with earlier runs. `--job <substring>` narrows to one job, `--sha <sha>` looks at an older commit.

A `pending` run has no result yet. Say so and analyze the latest finished run instead, or wait.

Done when: you have one `gs_url` per job to analyze.

### 2. Fetch the triage tier

```bash
scripts/main.py fetch <gs_url>          # prints the local run directory
```

This downloads job metadata, logs and junit for every step except the `gather-*` steps into `.context/openshift-ci/<org>_<repo>/<pr>/<job>/<build_id>/` under the repository root. Size and download time depend on the run. Rerunning transfers only what is missing.

Do not start with `--tier all` or a plain recursive copy. A run can exceed 1 GB and 14,000 objects, most of it a Prometheus dump and cluster state that answer nothing at this stage.

### 3. Summarize

```bash
scripts/main.py summary <run dir>
```

Prints the job, commit, result, the failed ci-operator steps and substeps with durations, each step's result with its path, and the junit reports with failure counts. If the optional step graph is missing, unreadable, malformed, or replaced by Prow's redaction notice, it warns and continues with the remaining sections. Use the per-step results and logs to identify the failure.

Read the failed substeps before anything else:

| Failed substep | Meaning |
|----------------|---------|
| `ipi-*`, `install`, cluster claim or lease steps | The cluster never came up: infrastructure, not the PR. |
| An image build step (`src`, `[input:…]`, `<image>`) | Build failure: read `artifacts/build-logs/<image>.log`. |
| The test step (for example `…-e2e`) | Tests failed: continue with step 4. |
| Only `gather-*` steps | Artifact collection failed. It does not explain a test failure; when a test step failed too, the gather failures are a side effect. |

### 4. List the failing tests

If the test JUnit report is missing, inspect the test step's `build-log.txt` for `=== RUN`, assertions, and timeout messages, then continue with step 5. A step timeout can stop report generation after tests have run; missing JUnit alone does not establish that tests never ran or that the failure was infrastructure.

```bash
scripts/main.py junit <run dir>/artifacts/<target>/<step>/artifacts/junit_report.xml \
  | jq -r '[.time, .name] | @tsv'
```

The `junit` command prints one JSON object per failed test: `file`, `suite`, `classname`, `name`, `time`, `message`, `output`. It keeps only leaf failures, because a Go parent test fails whenever a subtest does, so the report's own failure count overstates the number of distinct failures. `--all-failed` restores the parents.

`output` is cut to its last 2000 characters. Raise it for one test at a time, never for all:

```bash
scripts/main.py junit <junit file> --name '<regex on test name>' --max-chars 0 | jq -r .output
```

Skip `artifacts/junit_operator.xml` for test analysis: it restates the ci-operator steps that `summary` already listed.

### 5. Read the evidence

The junit output often holds only `subtest may have called FailNow on a parent test`. The assertion itself is in the step's `build-log.txt`, after the test's `=== RUN` line:

```bash
LOG=<run dir>/artifacts/<target>/<step>/build-log.txt

# Where each failure starts, in time order
rg -n 'Timed out after|Unexpected error|\[FAILED\]|panic:|^\s*--- FAIL' "$LOG" | cut -c1-200

# One failure with context
rg -n -A 12 '=== RUN\s+<full test name>$' "$LOG" | cut -c1-300
```

Always pipe through `cut -c1-300`. Assertion dumps print whole Kubernetes objects on one line, and a single unbounded line can be several kilobytes.

Work from the **first** failure in time. Later failures are often the same cause repeating, or a timeout cascade from a cluster the first failure left unhealthy. Group the failures by assertion message before deciding how many causes there are.

Done when: you can quote the assertion for each distinct cause.

### 6. Escalate to cluster state only if needed

When the assertion says what was wrong but not why (a deployment never became ready, a condition stayed `False`), fetch the cluster state:

```bash
scripts/main.py fetch <gs_url> --step gather-extra     # can exceed 1 GB even without archives
scripts/main.py fetch <gs_url> --tier gather           # all gather-* steps, no archives
```

Start with `--step gather-extra`; it has the events, pod status and pod logs. Add the other gather steps only when it does not have what you need.

Then read [references/artifacts.md](references/artifacts.md) for the layout and the queries for events, pod status, and pod logs. Query the JSON with `jq`; do not open these files whole.

The gather steps run after the tests and their cleanup, so resource dumps show the cluster at the end of the job, not at the moment of the failure. A deployment at 0 replicas or a missing pod may only mean the suite had already torn it down. Use event timestamps and pod logs to establish what was true when the test failed, and check that an error you find was not produced on purpose by another test (a fixture such as a restrictive quota) before calling it the cause.

### 7. Report

State, in this order:

1. The run: job, build ID, commit, Prow URL.
2. The failed step, and whether it is infrastructure, a build, or tests.
3. Each distinct cause: the tests it explains, the quoted assertion or log line, and the file path and line it came from.
4. What you did not determine, and which artifact would settle it.
5. Whether it looks related to the PR's change or like a flake. Check with `scripts/main.py runs <pr> --list`: the same job passing on the same commit points to a flake; the same tests failing on every run points to the change.

## Rules

| Rule | Why |
|------|-----|
| Do not comment `/retest` or `/test` on the PR on your own. | A comment is a write, visible to others, and starts a multi-hour job. It needs the user's explicit confirmation of the exact command (see `dev-gh` when available). |
| Do not conclude "flake" from one run. | It is the conclusion that ends an investigation early. Support it with a passing run of the same job on the same commit, or say it is unverified. |
| Do not report a cause without a quoted line and its path. | A failed step name is where it failed, not why. |
| Do not read `build-log.txt`, junit XML or `gather-extra` JSON whole. | They run to megabytes; search them, then read the lines around the match. |
| Do not delete or re-download a run directory to "start clean". | `fetch` is incremental; the data of a finished run never changes. |
