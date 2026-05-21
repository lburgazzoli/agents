---
name: agentready
description: Assess a repository for AI-assisted development readiness using AgentReady.
  Accepts a local path, GitHub owner/repo, full GitHub URL, or "." for the current
  directory. Use when the user asks to assess, score, or evaluate a repo's agent-readiness.
---

# AgentReady Assessment

Assess a git repository for AI-assisted development readiness using the AgentReady container image.

## Input

`$ARGUMENTS` contains the target:
- Empty or `.` — assess the current working directory
- `/absolute/path` — assess a local repo at that path
- `owner/repo [branch]` — clone from GitHub and assess (default branch if omitted)
- `https://github.com/owner/repo [branch]` — clone from GitHub and assess

Optional flags appended after the target:
- `--output-dir <path>` — override the default report directory (default: `.context/agentready/<repo>@<branch>`)
- `--verbose` — show detailed progress
- `--exclude <attr>` — skip specific attributes (repeatable, e.g. `--exclude test_execution --exclude type_annotations`)

## Steps

1. **Parse input**
   - If empty or `.`, set `REPO_PATH` to the current working directory
   - If an absolute path, set `REPO_PATH` to that path
   - If it matches `owner/repo` or a GitHub URL, extract the slug and proceed to step 2
   - Extract any `--output-dir`, `--verbose`, or `--exclude <attr>` flags from the arguments

2. **Clone if GitHub target**
   Follow `dev-context` and `dev-git` conventions to clone into `.context/repos/<org>/<repo>@<branch>`.
   If already cloned, pull to refresh. Set `REPO_PATH` to the absolute path of the clone directory.

3. **Prepare output directory**
   If `--output-dir` was provided, use that path as `OUTPUT_DIR`.
   Otherwise, derive `REPO_NAME` from the repo directory name and `BRANCH` from `git -C <REPO_PATH> rev-parse --abbrev-ref HEAD`, then set `OUTPUT_DIR` to `.context/agentready/${REPO_NAME}@${BRANCH}`.
   ```bash
   mkdir -p "${OUTPUT_DIR}"
   ```

4. **Pull the container image** (first run only)
   ```bash
   podman pull ghcr.io/ambient-code/agentready:latest
   ```

5. **Run assessment**
   ```bash
   podman run --rm \
     --user "$(id -u):$(id -g)" \
     --userns=keep-id \
     -e GIT_CONFIG_COUNT=1 \
     -e GIT_CONFIG_KEY_0=safe.directory \
     -e GIT_CONFIG_VALUE_0=/repo \
     -v "<REPO_PATH>:/repo:ro,Z" \
     -v "$(pwd)/.context/agentready/${REPO_NAME}@${BRANCH}:/reports:Z" \
     ghcr.io/ambient-code/agentready:latest \
     assess /repo --output-dir /reports [--verbose] [--exclude <attr> ...]
   ```

6. **Read the JSON assessment** and present a rich summary:
   Parse `${OUTPUT_DIR}/assessment-latest.json` with jq to extract structured data.

   **Header:** overall score, certification level, attributes assessed/skipped count.

   **Passing attributes:** table with attribute name and score.

   **Failing attributes (all, sorted by tier/weight):** table with these columns:
   - Attribute name
   - Measured vs threshold (from `measured_value` and `threshold` fields)
   - Evidence details (join the `evidence` array — these contain the specific paths, counts, and checks that explain the failure)
   - Remediation summary (from `remediation.summary`)

   Use this jq to extract fail details:
   ```bash
   jq -r '.findings[] | select(.status == "fail") | [.attribute.id, .attribute.tier, .measured_value, .threshold, (.evidence | join("; ")), .remediation.summary] | @tsv' "${OUTPUT_DIR}/assessment-latest.json"
   ```

   **Footer:** path to full HTML report at `${OUTPUT_DIR}/report-latest.html`.

## Troubleshooting

- **SELinux / permission errors**: the command already uses `:Z` mounts, `--userns=keep-id`, and `--user` flags for rootless podman
- **Git dubious ownership**: the `GIT_CONFIG_*` env vars handle this
- **Large repos**: agentready may warn about repo size; pass `-i` to the assess command if interactive confirmation is needed (not typical in container mode)
