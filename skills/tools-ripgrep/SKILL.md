---
name: tools-ripgrep
description: >
  Prefer rg (ripgrep) over find and grep for code search and file discovery.
  Triggers when searching file contents, finding files by name or glob,
  listing files by type, or running grep -r / find -name / find | xargs grep.
user-invocable: false
---

# ripgrep (rg) Guidelines

Prefer `rg` over `grep -r` and `find -name` for all code-search and file-discovery tasks. It respects `.gitignore` by default, searches recursively, and produces compact output.

## Command decision tree

| Need | Command | Example |
|------|---------|---------|
| Search file contents | `rg pattern` | `rg 'func main'` |
| Case-insensitive search | `rg -i pattern` | `rg -i 'readme'` |
| Word-boundary match | `rg -w pattern` | `rg -w 'Error'` |
| Fixed string (no regex) | `rg -F pattern` | `rg -F 'map[string]interface{}'` |
| Which files contain X | `rg -l pattern` | `rg -l 'FinalizerName'` |
| Count matches per file | `rg -c pattern` | `rg -c 'import'` |
| Search one language only | `rg -t lang pattern` | `rg -t go 'context.Context'` |
| Exclude one language | `rg -T lang pattern` | `rg -T test 'Deprecated'` |
| Search with context | `rg -C N pattern` | `rg -C 3 'func TestFoo'` |
| Context before only | `rg -B N pattern` | `rg -B 5 'panic('` |
| Context after only | `rg -A N pattern` | `rg -A 10 'func New'` |
| Multiline pattern | `rg -U pattern` | `rg -U 'struct \{[^}]*\}'` |
| List all files (replaces find) | `rg --files` | `rg --files` |
| List files matching glob | `rg --files -g 'glob'` | `rg --files -g '*.yaml'` |
| List files for a language | `rg --files -t lang` | `rg --files -t go` |
| Structured output for parsing | `rg --json pattern` | `rg --json 'func main' \| head -20` |
| Deterministic ordering | `rg --sort path pattern` | `rg --sort path -l 'init'` |
| Limit matches per file | `rg -m N pattern` | `rg -m 1 'package '` |
| Match statistics | `rg --stats pattern` | `rg --stats 'error' >/dev/null` |

## File discovery: rg --files replaces find

For locating files by name or extension within a code repository, `rg --files` is faster and automatically excludes `.gitignore`-listed paths.

```bash
# list all Go files (replaces: find . -name "*.go")
rg --files -g '*.go'

# list all Go files (alternative: type-aware)
rg --files -t go

# find a file by name (replaces: find . -name "config.yaml")
rg --files -g 'config.yaml'

# find files matching a partial name
rg --files -g '*controller*'

# find files in a specific directory
rg --files src/pkg/

# combine glob include with glob exclude
rg --files -g '*.go' -g '!*_test.go'

# case-insensitive glob matching
rg --files --iglob 'readme*'
```

## Content search: rg replaces grep -r

```bash
# basic recursive search (replaces: grep -r 'pattern' .)
rg 'pattern'

# scoped to language (replaces: find . -name "*.go" | xargs grep 'pattern')
rg -t go 'pattern'

# scoped to directory
rg 'pattern' pkg/controller/

# fixed string — no regex escaping needed
rg -F 'map[string][]byte'

# whole-line match
rg -x 'package main'

# invert match
rg -v 'vendor' -l 'pattern'
```

## Agent-optimized patterns

Minimize output tokens. Prefer the narrowest output format that answers the question.

```bash
# Q: "Does any file contain X?" — file list only, no content
rg -l 'FinalizerName'

# Q: "How many files contain X?" — count only
rg -l 'FinalizerName' | wc -l

# Q: "How many matches of X?" — per-file counts
rg -c 'TODO'

# Q: "What does the match look like?" — limit matches per file
rg -m 3 'func.*Handler'

# Exclude directories without piping
rg -g '!vendor' -g '!node_modules' -g '!.git' 'pattern'

# Exclude test files
rg -g '!*_test.go' -g '!*_test.py' 'pattern'

# Type exclusion (built-in, cleaner than globs)
rg -T test 'pattern'
```

### Chaining multiple queries

Combine related searches in a single Bash call to reduce tool invocations.

```bash
# Find interface and all implementations
rg -t go 'type Reconciler interface' && \
rg -t go 'func.*Reconcile\(ctx'

# Find struct definition, constructor, and usage
rg -t go 'type Config struct' && \
rg -t go 'func NewConfig' && \
rg -t go -l 'NewConfig('

# Inventory: list files, count matches, show sample
rg --files -t go | wc -l && \
rg -c 'context\.Context' -t go --sort path && \
rg -m 1 'context\.Context' -t go
```

## Key flags reference

| Flag | Purpose | Notes |
|------|---------|-------|
| `-i` | Case-insensitive | |
| `-w` | Word boundary | Wraps pattern in `\b...\b` |
| `-x` | Full line match | Anchors pattern to `^...$` |
| `-F` | Fixed string (no regex) | Use for literals with special chars |
| `-U` | Multiline mode | Allows `.` to match `\n` |
| `-l` | Files-with-matches only | No content output |
| `-c` | Count per file | Compact summary |
| `-m N` | Max N matches per file | Limits output |
| `-t type` | Include file type | `go`, `py`, `yaml`, `json`, `md`, `ts`, `rust` |
| `-T type` | Exclude file type | `-T test` excludes test files |
| `-g 'glob'` | Include glob | `-g '*.go'`, `-g 'pkg/**'` |
| `-g '!glob'` | Exclude glob | `-g '!vendor'`, `-g '!*_test.go'` |
| `--iglob` | Case-insensitive glob | `--iglob 'makefile*'` |
| `--sort path` | Deterministic order | Useful for reproducible output |
| `--json` | Structured JSON output | For programmatic parsing |
| `--stats` | Match statistics | Counts files, lines, matches |
| `-A N` / `-B N` / `-C N` | After / Before / Context lines | Surrounding context |
| `--no-ignore` | Disable .gitignore filtering | When you need ignored files |
| `--hidden` | Search hidden files | Dot-files/dot-dirs |
| `--files` | List files (no search) | Replaces `find -type f` |

## Anti-patterns

| Do not | Why | Do instead |
|--------|-----|------------|
| `find . -name "*.go" \| xargs grep 'pat'` | Two processes, no .gitignore respect, quoting issues | `rg -t go 'pat'` |
| `grep -r 'pattern' .` | Searches .git, vendor, node_modules; no type filtering | `rg 'pattern'` |
| `find . -type f` for file listing in code repos | No .gitignore, includes binary/generated files | `rg --files` |
| `rg 'pattern' \| grep 'filter'` | Piping rg to grep; rg can filter itself | `rg 'pattern' -g 'glob'` or `rg 'pattern' path/` |
| `rg 'pattern' \| wc -l` for file count | Counts lines of output, not files | `rg -l 'pattern' \| wc -l` or `rg -c 'pattern'` |
| `rg 'pattern'` without path/type scope in large repos | Unbounded search floods context | Add `-t type`, `-g glob`, or a directory argument |
| `rg --files \| grep '\.go$'` | Shell grep on file list; rg has built-in globs | `rg --files -g '*.go'` or `rg --files -t go` |
| `rg -e 'a' \| rg -e 'b'` for AND logic | Pipe loses file context, two processes | `rg 'a' -l \| xargs rg 'b'` or `rg 'a.*b\|b.*a'` |

## Scope boundary — when find is still correct

`rg` replaces `find` and `grep` for content search and file-name discovery in code repositories. It does NOT replace `find` for:

| Need | Tool | Example |
|------|------|---------|
| Permission/ownership checks | `find -perm` / `-user` / `-group` | `find . -perm 755` |
| File age or modification time | `find -mtime` / `-newer` / `-mmin` | `find . -mtime -1` |
| File size filtering | `find -size` | `find . -size +10M` |
| Executing actions on results | `find -exec` / `-delete` | `find /tmp -name '*.log' -delete` |
| Empty file/directory discovery | `find -empty` | `find . -empty -type d` |
| Non-text / binary file operations | `find -type` with processing | `find . -name '*.bin' -exec md5sum {} +` |
| Symlink traversal / detection | `find -type l` / `-follow` | `find . -type l` |
| Searching gitignored files | `find` or `rg --no-ignore` | `find . -name '*.log'` |
