# Vanilla Gomega Test Style

Rewrites kubebuilder's scaffolded Ginkgo tests to vanilla Go tests with Gomega dot imports.

## Dependencies

```bash
go get github.com/onsi/gomega
go get -u github.com/onsi/ginkgo/v2@none
```

If using k3senvtest, also add:
```bash
go get github.com/lburgazzoli/gomega-matchers
```

## Test Setup (replace `suite_test.go`)

### With k3senvtest

```go
package controller_test

import (
    "context"
    "testing"

    . "github.com/onsi/gomega"
    "github.com/lburgazzoli/k3s-envtest/pkg/k3senv"
    ctrl "sigs.k8s.io/controller-runtime"
)

func TestControllers(t *testing.T) {
    g := NewWithT(t)

    env, err := k3senv.New(
        k3senv.WithManifests("../../config/crd/bases"),
        k3senv.WithScheme(scheme),
    )
    g.Expect(err).NotTo(HaveOccurred())

    ctx, cancel := context.WithCancel(context.Background())
    t.Cleanup(func() {
        cancel()
        _ = env.Stop(context.Background())
    })

    g.Expect(env.Start(ctx)).To(Succeed())

    mgr, err := ctrl.NewManager(env.Config(), ctrl.Options{Scheme: scheme})
    g.Expect(err).NotTo(HaveOccurred())

    g.Expect((&WidgetReconciler{
        Client: mgr.GetClient(),
        Scheme: mgr.GetScheme(),
    }).SetupWithManager(mgr)).To(Succeed())

    go func() { _ = mgr.Start(ctx) }()

    t.Run("widget reconciliation", func(t *testing.T) {
        testWidgetReconciliation(t, env.Client())
    })
}
```

### With envtest

```go
package controller_test

import (
    "context"
    "path/filepath"
    "testing"

    . "github.com/onsi/gomega"
    "sigs.k8s.io/controller-runtime/pkg/envtest"
    ctrl "sigs.k8s.io/controller-runtime"
)

func TestControllers(t *testing.T) {
    g := NewWithT(t)

    testEnv := &envtest.Environment{
        CRDDirectoryPaths:     []string{filepath.Join("..", "..", "config", "crd", "bases")},
        ErrorIfCRDPathMissing: true,
    }

    cfg, err := testEnv.Start()
    g.Expect(err).NotTo(HaveOccurred())
    t.Cleanup(func() { _ = testEnv.Stop() })

    g.Expect(appsv1.AddToScheme(scheme)).To(Succeed())

    mgr, err := ctrl.NewManager(cfg, ctrl.Options{Scheme: scheme})
    g.Expect(err).NotTo(HaveOccurred())

    g.Expect((&WidgetReconciler{
        Client: mgr.GetClient(),
        Scheme: mgr.GetScheme(),
    }).SetupWithManager(mgr)).To(Succeed())

    ctx, cancel := context.WithCancel(context.Background())
    t.Cleanup(cancel)
    go func() { _ = mgr.Start(ctx) }()

    t.Run("widget reconciliation", func(t *testing.T) {
        testWidgetReconciliation(t, mgr.GetClient())
    })
}
```

## Controller Test (replace `*_controller_test.go`)

### With gomega-matchers (k3senvtest)

```go
import (
    k8sm "github.com/lburgazzoli/gomega-matchers/pkg/matchers/k8s"
    "github.com/lburgazzoli/gomega-matchers/pkg/matchers/jq"
)

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

### With plain Gomega (envtest)

```go
func testWidgetReconciliation(t *testing.T, cli client.Client) {
    g := NewWithT(t)
    ctx := context.Background()

    widget := &appsv1.Widget{
        ObjectMeta: metav1.ObjectMeta{
            Name:      "test-widget",
            Namespace: "default",
        },
        Spec: appsv1.WidgetSpec{Name: "test"},
    }

    g.Expect(cli.Create(ctx, widget)).To(Succeed())

    g.Eventually(func(g Gomega) {
        var fetched appsv1.Widget
        g.Expect(cli.Get(ctx, client.ObjectKeyFromObject(widget), &fetched)).To(Succeed())
        g.Expect(fetched.Status.Conditions).NotTo(BeEmpty())
    }, "30s", "250ms").Should(Succeed())
}
```

## Pattern

- Use `NewWithT(t)` for per-test Gomega instance
- Use `t.Run()` for subtests
- Use `t.Cleanup()` for teardown
- Always dot-import Gomega: `import . "github.com/onsi/gomega"`
