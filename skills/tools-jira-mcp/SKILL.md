---
name: tools-jira-mcp
description: Jira MCP tool patterns - tool selection, cloudId resolution, field formatting, and content conventions. Triggers when using mcp__jira__* tools.
user-invocable: false
---

# Jira MCP Patterns

Reference for the Jira MCP server tools (`mcp__jira__*`).

## Availability

MCP tools are present only when the Jira MCP server is connected (via `/mcp`). If `mcp__jira__*` tools are not in the available tool list, fall back to `acli` CLI - see `tools-jira-cli` skill.

## cloudId Resolution

Most MCP tools require a `cloudId` parameter. Resolution strategy:

1. Try the site hostname directly (e.g. `issues.redhat.com`) as `cloudId`
2. If that fails, call `mcp__jira__getAccessibleAtlassianResources` to discover available cloud IDs
3. Reuse the resolved cloudId for all subsequent calls in the session

Tools that do NOT require cloudId: `getAccessibleAtlassianResources`, `atlassianUserInfo`, `search`, `fetch`.

## Tool Selection

| Operation | Tool | Key params |
|-----------|------|------------|
| View issue | `getJiraIssue` | `issueIdOrKey`, `fields[]` |
| JQL search | `searchJiraIssuesUsingJql` | `jql`, `fields[]`, `maxResults` |
| General search | `search` | `query` |
| Create issue | `createJiraIssue` | `projectKey`, `issueTypeName`, `summary` |
| Edit issue | `editJiraIssue` | `issueIdOrKey`, `fields{}` |
| Add comment | `addCommentToJiraIssue` | `issueIdOrKey`, `commentBody` |
| Get transitions | `getTransitionsForJiraIssue` | `issueIdOrKey` |
| Transition issue | `transitionJiraIssue` | `issueIdOrKey`, `transition.id` |
| Create link | `createIssueLink` | `inwardIssue`, `outwardIssue`, `type` |
| Get link types | `getIssueLinkTypes` | *(cloudId only)* |
| Get remote links | `getJiraIssueRemoteIssueLinks` | `issueIdOrKey` |
| List projects | `getVisibleJiraProjects` | *(cloudId only)* |
| Project issue types | `getJiraProjectIssueTypesMetadata` | `projectIdOrKey` |
| Field metadata | `getJiraIssueTypeMetaWithFields` | `projectIdOrKey`, `issueTypeId` |
| Lookup user | `lookupJiraAccountId` | `searchString` |
| User info | `atlassianUserInfo` | *(no params)* |
| Add worklog | `addWorklogToJiraIssue` | `issueIdOrKey`, `timeSpent` |
| Fetch by ARI | `fetch` | `id` (ARI string) |

## Content Format

- Use `responseContentFormat: "markdown"` for readable output
- Use `contentFormat: "markdown"` when writing descriptions or comments
- Default is ADF (JSON) which is verbose - always override to markdown

## Field Selection

Pass specific fields in the `fields` array to reduce response size:

- Single issue: `["summary", "status", "issuetype", "assignee", "components", "labels", "description", "parent"]`
- Search results: `["summary", "status", "issuetype", "assignee"]`
- With links: add `"issuelinks"` to the fields array

## Issue Links

No dedicated list-links tool. To get links:

- Include `"issuelinks"` in the `fields` array of `getJiraIssue`
- For remote links (external URLs), use `getJiraIssueRemoteIssueLinks`

## Pagination

- `maxResults` capped at 100 per request
- Use `nextPageToken` for subsequent pages
- For large result sets, paginate until all results are collected or suggest the user refine the query

## Transitions

Always call `getTransitionsForJiraIssue` first to discover valid transition IDs before calling `transitionJiraIssue`.

## Important

- Read-only by default: do NOT create, edit, transition, or comment on issues unless the user explicitly asks
