---
name: tools-skillsaw
description: >
  Lint and fix AI agent instruction files (SKILL.md, CLAUDE.md, plugin.json)
  using skillsaw. Triggers when linting skills, validating plugin structure,
  checking instruction quality, or running skillsaw commands.
user-invocable: false
---

# skillsaw

Linter for AI agent instruction files. Runs via container image `ghcr.io/stbenjam/skillsaw:latest`.

## Container invocation

```bash
# podman (rootless) — use --userns=keep-id and :Z for SELinux
# Always use --format json for post-processing (see "Post-run validation")
podman run --rm --userns=keep-id -v $(pwd):/workspace:Z ghcr.io/stbenjam/skillsaw:latest -v --format json 2>/dev/null

# docker
docker run --rm -v $(pwd):/workspace ghcr.io/stbenjam/skillsaw:latest -v --format json 2>/dev/null
```

## Command decision tree

| Need | Command |
|------|---------|
| Lint current directory | `skillsaw` |
| Verbose (info-level findings) | `skillsaw -v` |
| Warnings as errors | `skillsaw --strict` |
| Apply safe structural fixes | `skillsaw fix` |
| Fix with LLM (content rules) | `skillsaw fix --llm` |
| Preview LLM fixes | `skillsaw fix --llm --dry-run` |
| Specify LLM model | `skillsaw fix --llm --model vertex_ai/claude-sonnet-4-6` |
| Auto-apply without prompt | `skillsaw fix -y` |
| Visualize lint tree | `skillsaw tree` |
| Generate docs | `skillsaw docs --format markdown -o docs/README.md` |
| List all rules | `skillsaw list-rules` |
| Generate config | `skillsaw init` |

## Output formats

```bash
# JSON to stdout
skillsaw --format json

# SARIF to file
skillsaw --output results.sarif

# HTML report
skillsaw --output report.html
```

## Key flags

| Flag | Purpose |
|------|---------|
| `-v` | Info-level messages |
| `--strict` | Warnings become errors (exit 1) |
| `--fix` | Apply safe auto-fixes during lint |
| `--llm` | LLM-powered content fixes (with `fix` or `--fix`) |
| `--dry-run` | Preview changes without writing |
| `--format {text,json,sarif,html}` | Output format |
| `--output FILE` | Write to file (format inferred from extension) |
| `-c CONFIG` | Override config path |
| `--type TYPE` | Override repo type detection |
| `--workers N` | Parallel LLM workers (default: 4) |
| `--max-iterations N` | Max fix iterations per file (default: 3) |
| `-y` | Auto-apply without confirmation |

## Exit codes

- `0` — no errors (warnings OK unless `--strict`)
- `1` — errors found or warnings in strict mode

## Config

`.skillsaw.yaml` at repo root. Generate a default with `skillsaw init`.

```yaml
version: "1"
rules:
  rule-name:
    enabled: false        # disable a rule
    severity: warning     # override severity
exclude:
  - "vendor/**"
  - ".context/**"
```

## Post-run validation

Always run skillsaw with `--format json` and post-process the output to filter false positives before presenting results.

### Workflow

1. Parse `.violations[]` from the JSON output
2. For `content-unlinked-internal-reference` findings, extract the path from the message (`Unlinked path reference: '<path>'`) and suppress the finding if **any** of these apply:
   - **Path does not exist in the repository** — run `test -e <path>` from the repository root; non-existent paths are templates or examples for generated projects
   - **Path is inside a fenced code block** — read the source file and check whether the flagged line is between `` ``` `` fences
   - **String is not a file path** — MIME types (`application/...`), org/repository slugs, or URL fragments
3. For `content-inconsistent-terminology` findings, suppress when variants are domain-appropriate:
   - `repo` in path templates (`owner/repo`, `<repo>`, `.context/repos/`) vs `repository` in prose — path templates are structural, not terminology choices
   - `directory` vs `folder` — `folder` is correct for Google Drive, `directory` for filesystem paths
   - `function` vs `method` — `function` is correct for Go/git contexts, `method` for API/OOP contexts
4. For `content-actionability-score` findings, suppress when the file is a `references/` lookup table, catalog, or pattern guide — these are descriptive by nature and low verb/command density is expected
5. Report all other violations unchanged, noting how many findings were suppressed per rule
