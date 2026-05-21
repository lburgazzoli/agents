---
name: jira-tree
description: Find issues in a Jira hierarchy (parent, children, siblings, links) filtered by component and team label. Defaults to AI Core Platform / aicp-team-*. Use with a RHAISTRAT or RHAIRFE issue key.
---

# Jira Issue Tree

Recursively walk a Jira issue's hierarchy and collect related issues that match the target component or team label. Prefers MCP tools when available, falls back to acli CLI.

## Input

`$ARGUMENTS` contains:
- **Required:** issue key (e.g. `RHAISTRAT-1235`)
- **Optional:** `component=<name>` (default: `AI Core Platform`)
- **Optional:** `team=<label-prefix>` (default: `aicp-team-`)
- **Optional:** `depth=<number>` (default: `4`) - max recursion depth from root

## Tool Selection

**Prefer MCP** (if `mcp__jira__*` tools are available):
- Single issue: `mcp__jira__getJiraIssue` with `fields: ["summary", "status", "issuetype", "components", "labels", "parent", "issuelinks"]`
- Child search: `mcp__jira__searchJiraIssuesUsingJql` with JQL `parent = <key> AND status not in (Closed, Resolved)` and `fields: ["summary", "status", "issuetype", "components", "labels"]`
- Issue links: include `"issuelinks"` in `fields` of `getJiraIssue` (no separate list-links tool in MCP)
- See `tools-jira-mcp` skill for cloudId resolution and pagination

**Fallback to CLI** (if MCP unavailable):
- See `tools-jira-cli` skill for acli command syntax and common query patterns

## Steps

1. **Parse arguments** for the issue key and optional overrides.

2. **Fetch the root issue** with fields: summary, status, issuetype, components, labels, parent, issuelinks. Parse to extract parent key, components, labels, and links.

3. **Fetch parent** (if exists) with fields: summary, status, issuetype, components, labels.

4. **Fetch ALL siblings** (children of parent): search with JQL `parent = <parent-key> AND status not in (Closed, Resolved)`, fields: key, summary, status, issuetype, components, labels. Paginate to get all results.

5. **Fetch linked issues**: extract links from root issue data (step 2). Fetch details for each linked issue. Also fetch links of the parent.

6. **Fetch children** of the root issue: search with JQL `parent = <issue-key> AND status not in (Closed, Resolved)`, same fields as step 4. Paginate.

7. **Uniform recursive descent** - maintain a queue of discovered matching issues (those with target component or team label). For each matching issue not yet expanded, fetch its children using the same JQL pattern.
   - Add any new matching children to the queue.
   - Continue until no new matching issues are discovered or the configured **depth** is reached from the root (to avoid runaway traversal).
   - This applies uniformly to: children of root, children of siblings, children of linked issues, and their descendants.

8. **Deduplicate** across all result sets.

9. **Filter**: only keep issues that meet at least one of:
    - Have the target component (e.g. `AI Core Platform`)
    - Have a label matching the team prefix (e.g. `aicp-team-*`)
    - Are the root issue itself (always included for context)

10. **Output a markdown table** grouped by hierarchy level (see format below).

11. **Output a team breakdown** summary table.

Parallelize independent calls aggressively - both MCP tool calls and acli commands support parallel execution.

## Output Format

Use relationship icons to make the table scannable:

- `★` - The issue itself
- `↑` - Parent
- `↔` - Sibling
- `→` - Linked issue
- `↓` - Child
- `↓ ↓` - Grandchild
- `↔ ↓` - Child of sibling

```markdown
## <issue-key>: <summary>

**Parent:** <parent-key> (<parent-summary>)

### Matching issues (component = <component> or label = `<team-prefix>*`)

| Key | Summary | Status | Rel | `<team-prefix>*` label |
|-----|---------|--------|:---:|-----|
| [KEY](https://issues.redhat.com/browse/KEY) | ... | ... | ★/↔/→/↓/↓ ↓/↔ ↓ | label or *(none)* |

### Team breakdown

| Team Label | Count |
|------------|-------|
| ... | ... |
```

Group rows by hierarchy level with **bold section headers** in the table (Strategy, RFE, Linked, Children, Grandchildren, etc.).

## Important

- Prefer MCP tools when available; fall back to acli CLI (see `tools-jira-cli`). See `tools-jira-mcp` for MCP patterns.
- Read-only: do NOT create or modify Jira issues
