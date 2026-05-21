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
podman run --rm --userns=keep-id -v $(pwd):/workspace:Z ghcr.io/stbenjam/skillsaw:latest [command] [flags]

# docker
docker run --rm -v $(pwd):/workspace ghcr.io/stbenjam/skillsaw:latest [command] [flags]
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
