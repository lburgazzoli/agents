---
name: tools-jira-cli
description: Jira CLI via acli - command syntax, JSON output processing with jq, and content conventions. Triggers when using acli workitem commands or writing Jira content.
user-invocable: false
---

# Jira CLI Guidelines

Use `acli` when MCP Jira tools (`mcp__jira__*`) are not available. The `jira-query` and `jira-tree` skills delegate here as a fallback.

## Content conventions

When working with Jira issues:

- Keep content minimal and concise - avoid verbosity
- Use lowercase unless semantically required (proper nouns, acronyms)
- Use hyphens (-) instead of em-dashes (—)
- Prefer prose or short lists over endless bullet points
- Avoid repetition of information
- Use `acli` (Atlassian CLI) for all Jira interaction - read-only unless the user explicitly asks to create or modify
- Always use `jq` for JSON processing, extraction, and transformation - never python, awk, or grep on JSON output

## acli quick reference

```bash
# view an issue
acli jira workitem view KEY-123 --fields summary,status,description

# view with JSON output (for jq processing)
acli jira workitem view KEY-123 --fields "*all" --json

# search with JQL
acli jira workitem search --jql "project = PROJ AND status != Closed" --fields key,summary,status --limit 20

# search with JSON/CSV output
acli jira workitem search --jql "..." --json
acli jira workitem search --jql "..." --csv

# comments and links
acli jira workitem comment list KEY-123
acli jira workitem link list KEY-123
```

## Key flags

- `--fields` - comma-separated field list (`*all`, `*navigable`, or specific fields)
- `--json` - JSON output (pipe to jq)
- `--csv` - CSV output
- `--limit N` - cap result count
- `--paginate` - fetch all pages
- `--count` - return count only

## Common query patterns

```bash
# single issue with standard fields
acli jira workitem view KEY-123 --fields summary,status,issuetype,assignee,components,labels,description,parent --json

# fetch links and comments
acli jira workitem link list KEY-123 --json
acli jira workitem comment list KEY-123 --json

# search with limit and field extraction
acli jira workitem search --jql "project = PROJ AND status != Closed" --fields key,summary,status,issuetype,assignee --limit 30 --json

# children of an issue (hierarchy traversal)
acli jira workitem search --jql 'parent = KEY-123 AND status not in (Closed, Resolved)' --fields key,summary,status,issuetype,components,labels --json --paginate
```
