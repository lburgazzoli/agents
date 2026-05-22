---
name: tools-podman
description: Container execution for Python, Go, and qmd using podman. Triggers when running scripts, executing code, or needing Python/Go/Node toolchains.
user-invocable: false
---

# Podman Container Execution

Run Python and Go scripts in container images from `tools/containers/` instead of local toolchains.

## Command Templates

```bash
# python
podman run --rm \
    -v "$(pwd)/.context:/work/.context:Z" \
    -v "/path/to/input:/input:ro,Z" \
    quay.io/lburgazzoli/ai-tools:python-3.12 script.py

# go
podman run --rm \
    -v "$(pwd)/.context:/work/.context:Z" \
    -v "/path/to/input:/input:ro,Z" \
    quay.io/lburgazzoli/ai-tools:go-1.25 run script.go
```

## Image availability

Before running a container, check that the image exists locally. If not, try pulling from quay.io. If the pull fails, build it from `tools/containers/`:

```bash
IMAGE=quay.io/lburgazzoli/ai-tools:TAG

podman image exists "$IMAGE" 2>/dev/null \
  || podman pull "$IMAGE" 2>/dev/null \
  || make -C tools/containers build/TAG
```

Available tags and their Containerfiles:

| Tag | Containerfile | Base |
|-----|--------------|------|
| `python-3.12` | `Containerfile.python-3.12` | `ubi9/python-312` |
| `go-1.25` | `Containerfile.go-1.25` | `ubi9/go-toolset:1.25` |
| `qmd` | `Containerfile.qmd` | `ubi10/nodejs-24` |
| `claude-code` | `Containerfile.claude-code` | — |

## Rules

- Always use `:Z` on volume mounts for SELinux relabeling
- `.context/` is always mounted read-write (scripts may write to `.context/tmp/`)
- All other volume mounts must be read-only (`:ro,Z`) unless the task explicitly requires writing
- Add `-v` mounts when the script requires access to files outside the working directory
