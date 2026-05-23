---
name: dev-kubebuilder
description: >
  Scaffold multi-API Kubebuilder projects with multigroup layout, webhooks, and
  API versioning. Use when the user asks to create a Kubernetes operator, scaffold
  a CRD project, add APIs, CRDs, or webhooks to a kubebuilder project, or set up
  a multi-group controller-runtime project. Triggers on: kubebuilder, operator,
  CRD, custom resource, controller-runtime, multi-group, conversion webhook.
user-invocable: true
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
---

# Kubebuilder Multi-API Project

Scaffold or extend a Kubebuilder operator project with multiple API groups, webhooks, and versioning.

**References** — read on demand, not upfront:
- [markers](references/markers.md) — CRD, validation, RBAC, webhook markers, cluster-scoped resources
- [patterns](references/patterns.md) — reconciler patterns, multigroup layout, external types, SetupWithManager
- [api-versioning](references/api-versioning.md) — hub-spoke conversion, storage version, deprecation
- [k3senvtest](references/e2e-k3senvtest.md) — k3s-envtest environment: Makefile, webhooks, gotchas
- [envtest](references/e2e-envtest.md) — standard envtest environment: Makefile, limitations
- [kind](references/e2e-kind.md) — Kind cluster environment: Makefile targets, setup script, e2e test scaffolding
- [test-gomega](references/test-gomega.md) — vanilla Go test scaffolding for both environments
- [test-ginkgo](references/test-ginkgo.md) — Ginkgo test scaffolding for both environments
- [webhook-strategy](references/webhook-strategy.md) — webhook decision tree: CRD markers vs ValidatingAdmissionPolicy vs classic webhook
- [main-config](references/main-config.md) — cobra+viper CLI, cache/client config, subcommand structure
- [project-maintenance](references/project-maintenance.md) — day-to-day operations, common workflows, key files

**Scope:** kubebuilder v4+ with `go/v4` plugin. Also applies to operator-sdk projects.

## Input

`$ARGUMENTS` should contain the project specification:

- **domain** — API group domain (e.g., `example.com`)
- **module** — Go module path (e.g., `github.com/user/my-operator`)
- **APIs** — one or more as `group/version/Kind` (e.g., `apps/v1alpha1/Widget`)
  - Append `+webhook` for defaulting + validation webhooks
  - Append `+cluster` for cluster-scoped resources
- **test environment** — selectable:
  - `+k3senvtest` — containerized k3s via testcontainers (real cluster behavior)
  - `+envtest` — standard controller-runtime envtest (in-process, kubebuilder default)
  - `+kind` — external Kind cluster with deployed controller (full e2e)
- **test style** — selectable:
  - `+gomega` — vanilla Go tests with Gomega (rewrites kubebuilder's scaffolded Ginkgo tests)
  - `+ginkgo` — keep kubebuilder's scaffolded Ginkgo tests as-is
- If not specified, infer from the prompt (e.g., "using k3senvtest" → k3senvtest, "using kind" → kind, "using gomega" → gomega)
- If still ambiguous, default to kubebuilder defaults: `+envtest +ginkgo`

Example: `domain=example.com module=github.com/acme/op api=apps/v1alpha1/Widget+webhook +k3senvtest +gomega`

If `$ARGUMENTS` is empty or incomplete, ask the user for the missing pieces:
1. Go module path
2. API domain
3. First API (group, version, kind)
4. Scope (namespaced or cluster)
5. Whether webhooks are needed
6. Whether additional APIs are planned
7. Test environment: k3senvtest, envtest, or kind
8. Test style: gomega (vanilla Go tests) or ginkgo (keep kubebuilder default)

Default version to `v1alpha1` if not specified.

## Prerequisites

Check before proceeding:

1. `go version` — require 1.22+
2. `kubebuilder version` — require v4+. If v3 detected, warn about incompatible flags and **stop**.
3. `make --version` — must be available
4. If k3senvtest or kind selected: container runtime (`podman` or `docker`) must be available

All kubebuilder commands below use `go run sigs.k8s.io/kubebuilder/v4/cmd@latest`. Never use `go install` or a bare `kubebuilder` binary.

## Steps

### Step 1: Detect project state and confirm plan

Check for a `PROJECT` file in the current directory.

- **If `PROJECT` exists** → existing project. Read it to understand domain, layout, and existing APIs. Detect test configuration:
  1. Check `plugins.dev-kubebuilder.lburgazzoli.github.io/v1` in the PROJECT file for stored choices.
  2. If not present, auto-detect by scanning test files with ripgrep **in this order** (earlier match wins, since gomega is also used inside ginkgo projects):
     1. `rg -l '//go:build e2e' test/` → kind (e2e build tag in `test/` directory)
     2. `rg -l 'k3senv\.New\(' internal/` → k3senvtest
     3. `rg -l 'envtest\.Environment' internal/` → envtest
     4. `rg -l 'RunSpecs\(' internal/` → ginkgo
     5. Only if ginkgo not found: `rg -l 'NewWithT\(' internal/` → gomega
  3. Skip to Step 3.
- **If no `PROJECT`** → new project. Proceed to Step 2.

Present a summary table to the user and ask for confirmation before proceeding:

| Group | Version | Kind | Scope | Webhooks | Testing |
|-------|---------|------|-------|----------|---------|

### Step 2: Initialize project

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest init --domain <domain> --repo <module> --multigroup
```

Always use `--multigroup` — it's easier to add API groups later than to migrate the layout.

After init, store the selected test configuration in the PROJECT file:

```bash
yq '.plugins."dev-kubebuilder.lburgazzoli.github.io/v1" = {"testEnvironment": "<envtest|k3senvtest|kind>", "testStyle": "<gomega|ginkgo>"}' -i PROJECT
```

This persists the choices so future invocations of this skill auto-detect them from the PROJECT file.

### Step 3: Rewrite main.go to cobra subcommand structure

Read [main-config](references/main-config.md). Rewrite `cmd/main.go` as root cobra command, create `cmd/operator/operator.go` as operator subcommand with viper config, cache stripping, and leader election enabled by default. Add `go get github.com/spf13/cobra github.com/spf13/viper`.

### Step 4: Create APIs

For each API in the plan:

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create api --group <group> --version <version> --kind <Kind>
```

For cluster-scoped resources, add `--namespaced=false`.

After each: note the generated files location. Read [multigroup layout](references/patterns.md#multigroup-directory-layout) if unsure about paths.

### Step 5: Scaffold stub types

Edit generated `*_types.go` files. Read [markers](references/markers.md) for syntax. Place stub Spec/Status fields with a few common markers as examples — the user fills in their actual domain model. Always include `Conditions []metav1.Condition` in Status.

### Step 6: Add validation / webhooks

Read [webhook-strategy](references/webhook-strategy.md) before creating any webhook. Evaluate in this order:

1. **CRD markers** — field constraints via `+kubebuilder:validation:*` or CEL. No webhook server needed.
2. **ValidatingAdmissionPolicy** (K8s 1.30+) — declarative validation, no Go code needed.
3. **Classic webhook** — only for mutation, conversion, external lookups, or cross-resource checks.

If a classic webhook is needed:

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create webhook --group <group> --version <version> --kind <Kind> \
  --defaulting --programmatic-validation
```

**Always scope webhooks** with namespace or object selectors — never intercept core types (pods, deployments) cluster-wide. Webhooks require cert-manager for TLS in-cluster — use `/dev-kind-setup`.

For conversion webhooks, read [api-versioning](references/api-versioning.md).

### Step 7: Review kustomize config

Review and update generated kustomize configuration:

1. `config/default/kustomization.yaml` — verify namespace and resource list
2. `config/manager/manager.yaml` — set resource limits and image
3. For webhooks, uncomment in `config/crd/kustomization.yaml`:
   - `patches/webhook_in_<kind>.yaml`
   - `patches/cainjection_in_<kind>.yaml`
4. For webhooks, enable in `config/default/kustomization.yaml`:
   - `../certmanager`
   - `../webhook`

### Step 8: Generate and validate

```bash
make manifests generate
make build
```

Review generated RBAC in `config/rbac/` — check for over-permissive roles.

Fix any compilation errors before proceeding.

### Step 9: Implement reconciler skeleton

Read [patterns](references/patterns.md) before implementing.

For each controller, scaffold:
- `SetupWithManager` with `For()`, `Owns()`, and `Watches()` for each owned/watched type
- `Reconcile` with error handling and requeue logic
- Status condition updates
- RBAC markers on the `Reconcile` method

For external types (watching CRDs from other operators), see the "Watching external types" section in [patterns](references/patterns.md).

### Step 10: Patch Makefile to `go run` style

Kubebuilder generates a Makefile that downloads tool binaries into `bin/` via `LOCALBIN`. **Patch it to follow `dev-go-project-new` conventions:** `go run <module>@<version>` for all tools, pinned versions in `_VERSION` variables at the top, no `bin/` directory.

Remove `LOCALBIN`, all binary download targets, and `bin/` references. Replace with `go run` variables:

```makefile
CONTROLLER_GEN_VERSION ?= <resolve current stable>
CONTROLLER_GEN = go run sigs.k8s.io/controller-tools/cmd/controller-gen@$(CONTROLLER_GEN_VERSION)
KUSTOMIZE_VERSION ?= <resolve current stable>
KUSTOMIZE = go run sigs.k8s.io/kustomize/kustomize/v5@$(KUSTOMIZE_VERSION)
```

Same pattern for `golangci-lint` and `govulncheck`. Pin each version — never `@latest`.

**If k3senvtest selected** — additionally:
- Remove `ENVTEST` variable and `setup-envtest` binary download
- Remove `KUBEBUILDER_ASSETS` from the `test` target
- Simplify `test` target to: `go test -race -count=1 ./...`

**If envtest selected** — convert `setup-envtest` to `go run` style:
```makefile
SETUP_ENVTEST_VERSION ?= <resolve current stable>
SETUP_ENVTEST = go run sigs.k8s.io/controller-runtime/tools/setup-envtest@$(SETUP_ENVTEST_VERSION)
```

**If kind selected** — read [kind](references/e2e-kind.md) for the full Makefile reference. Additionally:
- Remove `ENVTEST` variable, `setup-envtest` binary download, and `KUBEBUILDER_ASSETS`
- Simplify `test` target to: `go test -race -count=1 ./...`
- Add `KIND_VERSION`, `KIND`, `HELM_VERSION`, `HELM` tool variables (same `go run` pattern)
- Add `KIND_CLUSTER`, `KIND_NODE_IMAGE`, `CERT_MANAGER_VERSION` config variables
- Add `CONTAINER_TOOL`, `IMG`, `KUBECTL` variables
- Add `##@ Kind` section with `kind-create` and `kind-delete` targets
- Add `container-build`, `container-push` targets
- Add `test-e2e` target: `go test ./test/e2e/ -tags=e2e -v -timeout 30m`
- Add `deploy-kustomize`, `undeploy-kustomize`, `install`, `uninstall` targets
- Generate `hack/scripts/kind-setup.sh` and `chmod +x` it

### Step 11: Set up tests

Two independent choices: **environment** and **style**. Read both reference files:

1. **Environment** → read [k3senvtest](references/e2e-k3senvtest.md), [envtest](references/e2e-envtest.md), or [kind](references/e2e-kind.md) for dependencies, Makefile changes, and environment-specific config.
2. **Style** → read [test-gomega](references/test-gomega.md) or [test-ginkgo](references/test-ginkgo.md) for test scaffolding code matching both choices. Each style file has sections for both environments.

**If kind selected**: generate `test/e2e/` directory with build-tagged e2e test files (see [kind](references/e2e-kind.md) for scaffolding). Remove kubebuilder's scaffolded controller test files from `internal/controller/` since they depend on envtest. Add `.kube/` to `.gitignore`.

### Step 12: Run tests

```bash
make test
```

If tests fail:
- **k3senvtest**: read [k3senvtest](references/e2e-k3senvtest.md). Common issues: container runtime not available (see `dev-testcontainers` skill), k3s image not cached (first run pulls it).
- **envtest**: check `KUBEBUILDER_ASSETS` path, verify CRD directory paths are correct for multigroup layout.
- **kind**: run `make kind-create`, then `make container-build container-push`, `make deploy-kustomize`, `make test-e2e`. Common issues: container runtime not available, image not pushed (Kind needs to pull from a registry), cert-manager not ready yet, `KUBECONFIG` not set to `.kube/config`.

### Step 13: Summary

Report what was scaffolded: APIs created, webhooks configured, testing framework used, tests rewritten.

Kubebuilder's Makefile is the project's build system — use `dev-go-project` for ongoing make-based development (`make lint`, `make test`, `make build`).

## Rules

1. **Always use `--multigroup`** — it's easier to add API groups later than to migrate the layout.

2. **Always run `make manifests generate`** after any type or marker change. Never skip this.

3. **Consult [markers](references/markers.md)** for correct marker syntax. Do not guess marker names — they are exact strings.

4. **Use `+kubebuilder:storageversion`** on exactly one version per kind. Read [api-versioning](references/api-versioning.md) for the hub-spoke pattern.

5. **RBAC markers go on the reconciler's `Reconcile` method**, not on the types.

6. **`dev-go-project-new` Makefile conventions apply.** Kubebuilder generates a Makefile that downloads binaries into `bin/`. Step 10 patches it to use `go run <module>@<version>` with pinned `_VERSION` variables — the same conventions as `dev-go-project-new`. Never use `go install` or `@latest`.

7. **Test style is selectable.** If `+gomega` is selected, rewrite kubebuilder's Ginkgo tests to vanilla Go tests. If `+ginkgo` is selected, keep the scaffolded test structure. Either way, use dot imports for Gomega: `import . "github.com/onsi/gomega"`
