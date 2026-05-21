---
name: jira-query
description: Query Jira issues - accepts a natural language question, JQL, or issue key. Returns concise markdown results.
---

# Jira Query

General-purpose Jira querying. Prefers MCP tools when available, falls back to acli CLI.

## Input

`$ARGUMENTS` contains one of:
- **Issue key** (e.g. `RHAISTRAT-123`) - fetch and display that issue
- **JQL** (e.g. `project = RHAISTRAT AND status = "In Progress"`) - run the search
- **Natural language** (e.g. "open RFEs assigned to me") - translate to JQL and run

## Steps

1. **Determine query type** from arguments:
   - If it matches `[A-Z]+-\d+`, treat as an issue key
   - If it contains JQL keywords (`project =`, `status =`, `AND`, `OR`, `ORDER BY`), treat as JQL
   - Otherwise, translate natural language to JQL using known project keys (RHAISTRAT, RHAIRFE, RHOAIENG, OCPSTRAT)

2. **Single issue** (issue key):

   **Prefer MCP** (if `mcp__jira__*` tools are available):
   - `mcp__jira__getJiraIssue` with `issueIdOrKey` and fields `["summary", "status", "issuetype", "assignee", "components", "labels", "description", "parent", "issuelinks", "comment"]`
   - See `tools-jira-mcp` skill for cloudId resolution and field selection

   **Fallback to CLI** (if MCP unavailable):
   - See `tools-jira-cli` skill for acli command syntax

3. **Search** (JQL):

   **Prefer MCP**:
   - `mcp__jira__searchJiraIssuesUsingJql` with `jql`, `fields: ["summary", "status", "issuetype", "assignee"]`, `maxResults: 30`
   - See `tools-jira-mcp` skill for pagination

   **Fallback to CLI**:
   - See `tools-jira-cli` skill for acli search patterns

4. **Format output**:
   - Single issue: structured markdown with key fields, description excerpt, links, recent comments
   - Search results: markdown table

## Output Format

### Single issue

```markdown
## KEY-123: Summary

| Field | Value |
|-------|-------|
| Type | Story |
| Status | In Progress |
| Assignee | user@example.com |
| Components | AI Core Platform |
| Labels | aicp-team-foo |
| Parent | KEY-100 |

### Description
<first ~500 chars of description>

### Links
- blocks KEY-456 (Summary)
- is blocked by KEY-789 (Summary)

### Recent comments
- **2026-04-10** user@example.com: <excerpt>
```

### Search results

```markdown
## Results: <N> issues

| Key | Type | Summary | Status | Assignee |
|-----|------|---------|--------|----------|
| [KEY-1](https://issues.redhat.com/browse/KEY-1) | Story | ... | In Progress | ... |
```

## Important

- Prefer MCP tools (`mcp__jira__*`) when available; fall back to acli CLI (see `tools-jira-cli`) when MCP is not connected
- See `tools-jira-mcp` and `tools-jira-cli` skills for tool-specific patterns
- Read-only by default: do NOT create or modify Jira issues unless the user explicitly asks
- For large result sets, suggest the user refine their query
