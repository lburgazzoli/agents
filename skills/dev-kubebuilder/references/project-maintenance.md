# Kubebuilder Project Maintenance

Day-to-day operations for an existing kubebuilder project. This is the counterpart to the scaffolding workflow — use after the project is set up.

Assumes: kubebuilder v4+, Go 1.22+, multigroup layout, cobra subcommand structure (from [main-config](main-config.md)).

## Common Workflows

### After changing types or markers

See [markers](markers.md) for correct syntax.

```bash
make manifests generate
make build
```

### Add a new API to existing project

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create api --group <group> --version <version> --kind <Kind>
```

Then: scaffold stub types, update `cmd/operator/operator.go` to register the new controller, run `make manifests generate`.

### Add a new API version to existing kind

For example, adding `v1beta1` alongside `v1alpha1`:

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create api --group <group> --version v1beta1 --kind <Kind>
```

Then set up hub-spoke conversion — see [api-versioning](api-versioning.md). Designate one version as hub with `+kubebuilder:storageversion`, implement `ConvertTo`/`ConvertFrom` on spokes.

### Add validation or webhooks

Read [webhook-strategy](webhook-strategy.md) first — evaluate CRD markers and ValidatingAdmissionPolicy before creating a classic webhook.

If a classic webhook is needed:

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create webhook --group <group> --version <version> --kind <Kind> \
  --defaulting --programmatic-validation
```

Then: uncomment webhook/cert-manager patches in kustomize config, set replicas to 2 in `config/manager/manager.yaml`, scope with namespace/object selectors. For conversion webhooks, see [api-versioning](api-versioning.md).

### Add a new subcommand

See [main-config](main-config.md) for the cobra structure.

Create `cmd/<name>/<name>.go` with a cobra command, register it in `cmd/main.go` via `root.AddCommand()`.

### Update tool versions

Edit `_VERSION` variables at the top of the Makefile. Resolve current stable versions:

```bash
go list -m -versions sigs.k8s.io/controller-tools | tr ' ' '\n' | grep -vE 'rc|beta|alpha' | tail -1
```

Use the correct module path for each tool:
- `sigs.k8s.io/controller-tools` (controller-gen)
- `sigs.k8s.io/kustomize/kustomize/v5` (kustomize)
- `github.com/golangci/golangci-lint` (golangci-lint)

### Run tests

```bash
make manifests generate
make build
make test
```

Always run `make manifests generate` and `make build` before tests, especially after type changes.

- **k3senvtest**: requires container runtime (Podman/Docker) — see [e2e-k3senvtest](e2e-k3senvtest.md)
- **envtest**: requires `KUBEBUILDER_ASSETS` (handled by `setup-envtest` in Makefile) — see [e2e-envtest](e2e-envtest.md)

### Build and deploy

The `docker-build`/`docker-push` targets are kubebuilder's default names. They work with Podman via `podman-docker` package or `alias docker=podman`.

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

With Podman: `KIND_EXPERIMENTAL_PROVIDER=podman kind create cluster`. Use `/dev-kind-setup` to create a Kind cluster with cert-manager.

### Undeploy

```bash
make undeploy    # Remove operator deployment
make uninstall   # Remove CRDs from cluster
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

This layout reflects the cobra subcommand structure from the skill's scaffolding (see [main-config](main-config.md)). Vanilla kubebuilder projects have a single `cmd/main.go`.

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
| `Makefile` | Build system (`go run` style, no `bin/`) |

## Related Skills

- **`dev-go-project`** — Makefile-first development for ongoing build/test/lint
- **`dev-kind-setup`** — Kind cluster creation with cert-manager
- **`dev-testcontainers`** — Podman setup for container-based tests
