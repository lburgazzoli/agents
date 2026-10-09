# agents

A collection of reusable agent skills, installable via [Vercel Skills](https://github.com/vercel-labs/skills).

## Install

```bash
npx skills add lburgazzoli/agents
```

## Skills

| Skill | Description |
|-------|-------------|
| `agentready` | Assess repository AI-assisted development readiness |
| `dev-agent-loops` | Agent loop design patterns (loop types, stop conditions, verification) |
| `dev-context` | Conventions for cloning git repos into `.context/repos/` |
| `dev-gh` | GitHub CLI (gh) read patterns with a mandatory confirmation gate for writes |
| `dev-git` | Git history exploration and composed git commands |
| `dev-go-patterns` | Go design patterns (functional options, switch over if chains, etc.) |
| `dev-go-project` | Working in Go projects with Makefiles |
| `dev-go-project-new` | Bootstrap new Go projects |
| `dev-go-testing` | Gomega usage in Go tests (assertions, async, matchers) |
| `dev-k8s-controller` | Kubernetes controller implementation best practices (controller-runtime) |
| `dev-k8s-kubebuilder` | Scaffold multi-API Kubebuilder projects with multigroup layout and webhooks |
| `dev-kind-setup` | Create Kind cluster with cert-manager |
| `dev-openshift-ci` | Retrieve and analyze OpenShift CI (Prow) job failures on a pull request |
| `dev-skills` | Skill authoring guide |
| `dev-testcontainers` | Testcontainers setup with Podman/Docker |
| `jira-query` | Query Jira issues (natural language, JQL, or issue key) |
| `jira-tree` | Walk Jira issue hierarchy (parent, children, siblings, links) |
| `tools-containers` | Container image inspection with crane and skopeo, no pull or run |
| `tools-excalidraw` | Excalidraw diagram generation |
| `tools-gws` | Google Workspace CLI (gws) patterns |
| `tools-jira-cli` | Jira CLI (acli) patterns |
| `tools-jira-mcp` | Jira MCP tool patterns |
| `tools-kubectl` | kubectl/oc CLI patterns |
| `tools-podman` | Container execution via podman |
| `tools-ripgrep` | ripgrep search patterns |
| `tools-skillsaw` | skillsaw linter for AI agent instruction files |
