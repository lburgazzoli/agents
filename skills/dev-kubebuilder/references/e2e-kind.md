# Kind Cluster Environment Reference

Uses an external Kind cluster with the controller deployed as a container. Tests connect via kubeconfig and validate behavior end-to-end.

## Dependencies

```bash
go get github.com/lburgazzoli/gomega-matchers
```

Container runtime (`podman` or `docker`) must be available.

## Makefile

### Tool versions and commands

```makefile
KIND_VERSION    ?= v0.31.0
HELM_VERSION    ?= v4.2.0

KIND = go run sigs.k8s.io/kind@$(KIND_VERSION)
HELM = go run helm.sh/helm/v4/cmd/helm@$(HELM_VERSION)

CONTAINER_TOOL ?= podman
KUBECTL        ?= kubectl
```

### Container image

```makefile
IMG ?= ttl.sh/<project-name>-$(shell git rev-parse --short HEAD 2>/dev/null || echo dev):1h
```

`ttl.sh` is an ephemeral registry — images auto-expire after the TTL suffix. Suitable for CI and local development. Override `IMG` for production registries.

### Kind cluster targets

```makefile
KIND_CLUSTER         ?= <project-name>
KIND_NODE_IMAGE      ?=
CERT_MANAGER_VERSION ?= v1.17.2

##@ Kind

.PHONY: kind-create
kind-create: ## Create a Kind cluster and install cert-manager.
	KIND="$(KIND)" HELM="$(HELM)" CONTAINER_TOOL="$(CONTAINER_TOOL)" \
		KIND_CLUSTER=$(KIND_CLUSTER) KIND_NODE_IMAGE=$(KIND_NODE_IMAGE) \
		CERT_MANAGER_VERSION=$(CERT_MANAGER_VERSION) \
		hack/scripts/kind-setup.sh

.PHONY: kind-delete
kind-delete: ## Delete the Kind cluster.
	KIND_EXPERIMENTAL_PROVIDER="$(CONTAINER_TOOL)" $(KIND) delete cluster --name $(KIND_CLUSTER)
```

### Container build/push targets

```makefile
##@ Build

.PHONY: container-build
container-build: ## Build container image with the manager.
	$(CONTAINER_TOOL) build -f Containerfile --build-arg LDFLAGS="$(LDFLAGS)" -t ${IMG} .

.PHONY: container-push
container-push: ## Push container image.
	$(CONTAINER_TOOL) push ${IMG}
```

### Test targets

```makefile
.PHONY: test
test: manifests generate fmt vet ## Run unit tests.
	go test -race -count=1 ./...

.PHONY: test-e2e
test-e2e: ## Run e2e tests (assumes controller is already deployed).
	go test ./test/e2e/ -tags=e2e -v -timeout 30m
```

No `KUBEBUILDER_ASSETS`, no `ENVTEST`, no `setup-envtest`. Unit tests in `internal/` run without a cluster. E2e tests use a build tag and connect to the Kind cluster via kubeconfig.

### Deployment targets

```makefile
##@ Deployment

.PHONY: install
install: manifests ## Install CRDs into the K8s cluster specified in ~/.kube/config.
	@out="$$( $(KUSTOMIZE) build config/crd 2>/dev/null || true )"; \
	if [ -n "$$out" ]; then echo "$$out" | $(KUBECTL) apply -f -; else echo "No CRDs to install; skipping."; fi

.PHONY: uninstall
uninstall: manifests ## Uninstall CRDs from the K8s cluster specified in ~/.kube/config.
	@out="$$( $(KUSTOMIZE) build config/crd 2>/dev/null || true )"; \
	if [ -n "$$out" ]; then echo "$$out" | $(KUBECTL) delete --ignore-not-found=true -f -; else echo "No CRDs to delete; skipping."; fi

.PHONY: deploy-kustomize
deploy-kustomize: install ## Deploy controller via kustomize (CRDs + manifests).
	cd config/manager && $(KUSTOMIZE) edit set image controller=${IMG}
	$(KUSTOMIZE) build config/default | $(KUBECTL) apply -f -

.PHONY: undeploy-kustomize
undeploy-kustomize: ## Undeploy controller installed via kustomize.
	-$(KUSTOMIZE) build config/default | $(KUBECTL) delete --ignore-not-found=true -f -
	-@out="$$( $(KUSTOMIZE) build config/crd 2>/dev/null || true )"; \
	if [ -n "$$out" ]; then echo "$$out" | $(KUBECTL) delete --ignore-not-found=true -f -; fi
```

## Setup Script

Generate `hack/scripts/kind-setup.sh`:

```bash
#!/usr/bin/env bash
# Create a Kind cluster and install cert-manager.
#
# Environment:
#   KIND                 - kind command
#   HELM                 - helm command
#   CONTAINER_TOOL       - container runtime (default: podman)
#   KIND_CLUSTER         - cluster name
#   KIND_NODE_IMAGE      - node image (optional, e.g. kindest/node:v1.32.3)
#   CERT_MANAGER_VERSION - cert-manager version (default: v1.17.2)

set -euo pipefail

KIND="${KIND:-go run sigs.k8s.io/kind@v0.31.0}"
HELM="${HELM:-go run helm.sh/helm/v4/cmd/helm@v4.2.0}"
CONTAINER_TOOL="${CONTAINER_TOOL:-podman}"
CLUSTER="${KIND_CLUSTER:-kind}"
NODE_IMAGE="${KIND_NODE_IMAGE:-}"
CM_VERSION="${CERT_MANAGER_VERSION:-v1.17.2}"

if ${KIND} get clusters 2>/dev/null | grep -qw "${CLUSTER}"; then
    echo "Kind cluster '${CLUSTER}' already exists. Skipping creation."
    exit 0
fi

KIND_ARGS=(--name "${CLUSTER}")
if [ -n "${NODE_IMAGE}" ]; then
    KIND_ARGS+=(--image "${NODE_IMAGE}")
fi

echo "Creating Kind cluster '${CLUSTER}' with ${CONTAINER_TOOL} provider..."
KIND_EXPERIMENTAL_PROVIDER="${CONTAINER_TOOL}" ${KIND} create cluster "${KIND_ARGS[@]}"

echo "Installing cert-manager ${CM_VERSION}..."
${HELM} repo add jetstack https://charts.jetstack.io --force-update
${HELM} install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --version "${CM_VERSION}" \
    --set crds.enabled=true \
    --wait \
    --timeout 5m

KUBECONFIG_DIR=".kube"
mkdir -p "${KUBECONFIG_DIR}"
KIND_EXPERIMENTAL_PROVIDER="${CONTAINER_TOOL}" ${KIND} get kubeconfig --name "${CLUSTER}" 2>/dev/null > "${KUBECONFIG_DIR}/config"
echo "Kubeconfig written to ${KUBECONFIG_DIR}/config"

echo "Kind cluster '${CLUSTER}' ready with cert-manager ${CM_VERSION}."
```

Make the script executable: `chmod +x hack/scripts/kind-setup.sh`.

## E2e Test Scaffolding

Generate `test/e2e/e2e_test.go`:

```go
//go:build e2e

package e2e

import (
    "context"
    "fmt"
    "os"
    "testing"
    "time"

    . "github.com/onsi/gomega"

    "k8s.io/apimachinery/pkg/runtime"
    utilruntime "k8s.io/apimachinery/pkg/util/runtime"
    clientgoscheme "k8s.io/client-go/kubernetes/scheme"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/client/config"

    k8sm "github.com/lburgazzoli/gomega-matchers/pkg/matchers/k8s"

    // Import API types:
    // appsv1alpha1 "<module>/api/<group>/v1alpha1"
)

const (
    timeout  = 2 * time.Minute
    interval = 2 * time.Second
)

var (
    ctx       context.Context
    cancel    context.CancelFunc
    k8sClient client.Client
    k         *k8sm.Matcher

    testScheme = runtime.NewScheme()
)

func init() {
    utilruntime.Must(clientgoscheme.AddToScheme(testScheme))
    // utilruntime.Must(appsv1alpha1.AddToScheme(testScheme))
}

func TestMain(m *testing.M) {
    ctx, cancel = context.WithCancel(context.Background())
    defer cancel()

    cfg, err := config.GetConfig()
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to get kubeconfig: %v\n", err)
        os.Exit(1)
    }

    k8sClient, err = client.New(cfg, client.Options{Scheme: testScheme})
    if err != nil {
        fmt.Fprintf(os.Stderr, "Failed to create client: %v\n", err)
        os.Exit(1)
    }

    k = k8sm.New(k8sClient, testScheme)

    os.Exit(m.Run())
}
```

The test uses `config.GetConfig()` which reads from `KUBECONFIG` env var or `~/.kube/config`. The `kind-setup.sh` script writes kubeconfig to `.kube/config` — set `KUBECONFIG=.kube/config` or use the default location.

## E2e Test Workflow

```
make kind-create                    # Create cluster + cert-manager
make container-build container-push # Build and push image
make deploy-kustomize               # Deploy CRDs + controller
make test-e2e                       # Run e2e tests
make undeploy-kustomize             # Cleanup
make kind-delete                    # Tear down cluster
```

Override `KIND_NODE_IMAGE` to test against a specific Kubernetes version:
```
make kind-create KIND_NODE_IMAGE=kindest/node:v1.33.7
```

## Key Differences from envtest and k3senvtest

| Feature | envtest | k3senvtest | Kind |
|---------|---------|------------|------|
| Controller location | In-process | In-process | Deployed as container |
| Cluster lifecycle | Embedded in test | Embedded in test | External (`kind-create`/`kind-delete`) |
| Garbage collection | Not available | Works | Works |
| Namespace deletion | Stuck in Terminating | Works | Works |
| Built-in controllers | Absent | Present | Present |
| Webhook TLS | Manual setup | Auto-generated | cert-manager |
| Container runtime | Not needed | Required | Required |
| Container image | Not needed | Not needed | Required |
| K8s version matrix | Limited | k3s versions | Any `kindest/node` tag |
| Test speed | Fast (~1s startup) | Medium (~10-15s) | Slow (~30-60s cluster + deploy) |

## .gitignore Additions

```
.kube/
```

## Gotchas

- `kind-setup.sh` is idempotent — re-running skips cluster creation if the cluster already exists
- `KIND_EXPERIMENTAL_PROVIDER` tells Kind to use podman instead of docker
- The kubeconfig is written to `.kube/config` in the project root, not `~/.kube/config`
- Set `KUBECONFIG=.kube/config` before running `make test-e2e` or `kubectl` commands
- Images pushed to `ttl.sh` expire after the TTL suffix (e.g., `:1h`)
- For CI, use a matrix of `KIND_NODE_IMAGE` values to test multiple Kubernetes versions
