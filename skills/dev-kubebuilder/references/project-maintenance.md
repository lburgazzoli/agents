# Kubebuilder Project Maintenance

Day-to-day operations for an existing kubebuilder project. This is the counterpart to the scaffolding workflow — use after the project is set up.

## Common Workflows

### After changing types or markers

```bash
make manifests generate
make build
```

### Add a new API to existing project

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create api --group <group> --version <version> --kind <Kind>
```

Then: scaffold stub types, update `cmd/operator/operator.go` to register the new controller, run `make manifests generate`.

### Add webhooks to existing API

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create webhook --group <group> --version <version> --kind <Kind> \
  --defaulting --programmatic-validation
```

Then: uncomment webhook/cert-manager patches in kustomize config, set replicas to 2 in `config/manager/manager.yaml`.

### Regenerate Helm chart

```bash
make helm
```

This runs: `build-installer` → helm edit → `hack/scripts/helm-post-process.sh`.

Review changes in `config/chart/`. CRDs should be in `templates/`, not `crds/`.

### Add a new subcommand

Create `cmd/<name>/<name>.go` with a cobra command, register it in `cmd/main.go` via `root.AddCommand()`.

### Update tool versions

Edit `_VERSION` variables at the top of the Makefile. Resolve current stable versions:

```bash
go list -m -versions sigs.k8s.io/controller-tools/cmd/controller-gen | tr ' ' '\n' | tail -1
```

### Run tests

```bash
make test
```

- **k3senvtest**: requires container runtime (Podman/Docker)
- **envtest**: requires `KUBEBUILDER_ASSETS` (handled by `setup-envtest` in Makefile)

### Build and deploy

```bash
make docker-build IMG=<registry>/<name>:<tag>
make docker-push IMG=<registry>/<name>:<tag>
make deploy IMG=<registry>/<name>:<tag>
```

For Kind clusters (no push needed):

```bash
make docker-build IMG=<name>:test
kind load docker-image <name>:test
make deploy IMG=<name>:test
```

## PROJECT File Metadata

Test configuration is stored in `plugins.dev-kubebuilder.lburgazzoli.github.io/v1`:

```yaml
plugins:
  dev-kubebuilder.lburgazzoli.github.io/v1:
    testEnvironment: k3senvtest  # or envtest
    testStyle: gomega            # or ginkgo
```

## Key Files

| File | Purpose |
|------|---------|
| `PROJECT` | Kubebuilder metadata, API registry, plugin config |
| `cmd/main.go` | Root cobra command |
| `cmd/operator/operator.go` | Manager setup and start |
| `api/<group>/<version>/` | Type definitions and markers |
| `internal/controller/<group>/` | Reconcilers |
| `internal/webhook/<group>/<version>/` | Webhook handlers |
| `config/crd/bases/` | Generated CRD YAMLs |
| `config/rbac/` | Generated RBAC roles |
| `config/chart/` | Helm chart |
| `hack/scripts/` | Post-processing scripts |
| `Makefile` | Build system (`go run` style, no `bin/`) |
