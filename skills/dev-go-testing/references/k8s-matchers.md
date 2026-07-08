# K8s Operator Matchers

Repo: https://github.com/lburgazzoli/gomega-matchers

Project-specific matchers for Kubernetes operator tests using k3s-envtest.
Distilled from `skills/dev-k8s-kubebuilder/references/test-gomega.md`.

## Install

```bash
go get github.com/lburgazzoli/gomega-matchers
```

## Imports

```go
import (
    k8sm "github.com/lburgazzoli/gomega-matchers/pkg/matchers/k8s"
    "github.com/lburgazzoli/gomega-matchers/pkg/matchers/jq"
)
```

## k8sm — Kubernetes-aware matcher helper

```go
k := k8sm.New(cli, scheme)
```

`k` wraps a `client.Client` and `*runtime.Scheme` to provide K8s-aware matchers.

### Get and assert in one step

```go
// Polls until the object has the expected state
g.Eventually(k.Get(obj)).Should(
    jq.Match(`.status.conditions[] | select(.type == "Available") | .status == "True"`),
)
```

No need to call `cli.Get` separately — `k.Get` fetches the latest state each poll.

## jq — JSON-path assertions

```go
jq.Match(expr string) GomegaMatcher
```

Runs a jq expression against the JSON representation of the actual value.
Returns true if the expression output is truthy.

```go
// Assert a specific condition is set
g.Eventually(k.Get(widget)).Should(
    jq.Match(`.status.conditions[] | select(.type == "Available") | .status == "True"`),
)

// Assert a field value
g.Eventually(k.Get(pod)).Should(
    jq.Match(`.status.phase == "Running"`),
)

// Assert count
g.Eventually(k.Get(deployment)).Should(
    jq.Match(`.status.readyReplicas == 3`),
)
```

## Full test pattern

```go
func testWidgetReconciliation(t *testing.T, cli client.Client) {
    g := NewWithT(t)
    k := k8sm.New(cli, scheme)

    widget := &appsv1.Widget{
        ObjectMeta: metav1.ObjectMeta{
            Name:      "test-widget",
            Namespace: "default",
        },
        Spec: appsv1.WidgetSpec{Name: "test"},
    }

    g.Expect(cli.Create(context.Background(), widget)).To(Succeed())

    g.Eventually(k.Get(widget)).Should(
        jq.Match(`.status.conditions[] | select(.type == "Available") | .status == "True"`),
    )
}
```

## When to use

Use this pattern for K8s operator tests with k3s-envtest.
For plain Gomega without k8s-matchers, use the `Eventually(func(g Gomega){...})` pattern:

```go
g.Eventually(func(g Gomega) {
    var fetched appsv1.Widget
    g.Expect(cli.Get(ctx, client.ObjectKeyFromObject(widget), &fetched)).To(Succeed())
    g.Expect(fetched.Status.Conditions).NotTo(BeEmpty())
}, "30s", "250ms").Should(Succeed())
```

## Project convention

Always use k3s-envtest + gomega-matchers for K8s operator tests — not standard envtest,
not Ginkgo. See `dev-k8s-kubebuilder` skill for full test suite scaffolding.
