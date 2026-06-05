# Makefile Patching: go run Style

Kubebuilder generates a Makefile that downloads tool binaries into `bin/` via `LOCALBIN`. Patch it to follow `dev-go-project-new` conventions: `go run <module>@<version>` for all tools, pinned versions in `_VERSION` variables at the top, no `bin/` directory.

Remove `LOCALBIN`, all binary download targets, and `bin/` references. Replace with `go run` variables:

```makefile
CONTROLLER_GEN_VERSION ?= <resolve current stable>
CONTROLLER_GEN = go run sigs.k8s.io/controller-tools/cmd/controller-gen@$(CONTROLLER_GEN_VERSION)
KUSTOMIZE_VERSION ?= <resolve current stable>
KUSTOMIZE = go run sigs.k8s.io/kustomize/kustomize/v5@$(KUSTOMIZE_VERSION)
```

Same pattern for `golangci-lint` and `govulncheck`. Pin each version — never `@latest`.

## k3senvtest variant

- Remove `ENVTEST` variable and `setup-envtest` binary download
- Remove `KUBEBUILDER_ASSETS` from the `test` target
- Simplify `test` target to: `go test -race -count=1 ./...`

## envtest variant

Convert `setup-envtest` to `go run` style:

```makefile
SETUP_ENVTEST_VERSION ?= <resolve current stable>
SETUP_ENVTEST = go run sigs.k8s.io/controller-runtime/tools/setup-envtest@$(SETUP_ENVTEST_VERSION)
```

## kind variant

Read [kind](e2e-kind.md) for the full Makefile reference. Additionally:

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
