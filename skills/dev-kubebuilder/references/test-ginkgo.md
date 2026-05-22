# Ginkgo Test Style

Keeps kubebuilder's scaffolded Ginkgo test structure. Only the environment setup in `suite_test.go` needs to change when using k3senvtest.

## Dependencies

If using k3senvtest, add:
```bash
go get github.com/lburgazzoli/k3s-envtest
go get github.com/lburgazzoli/gomega-matchers
```

No dependency changes needed for envtest — kubebuilder scaffolds all required dependencies.

## suite_test.go

### With k3senvtest (replace BeforeSuite/AfterSuite)

Replace the `envtest.Environment` setup with `k3senv.New()`:

```go
var (
    env       *k3senv.K3sEnv
    k8sClient client.Client
    ctx       context.Context
    cancel    context.CancelFunc
)

var _ = BeforeSuite(func() {
    ctx, cancel = context.WithCancel(context.Background())

    var err error
    env, err = k3senv.New(
        k3senv.WithManifests("../../config/crd/bases"),
        k3senv.WithScheme(scheme),
    )
    Expect(err).NotTo(HaveOccurred())
    Expect(env.Start(ctx)).To(Succeed())

    k8sClient = env.Client()

    mgr, err := ctrl.NewManager(env.Config(), ctrl.Options{Scheme: scheme})
    Expect(err).NotTo(HaveOccurred())

    err = (&WidgetReconciler{
        Client: mgr.GetClient(),
        Scheme: mgr.GetScheme(),
    }).SetupWithManager(mgr)
    Expect(err).NotTo(HaveOccurred())

    go func() { defer GinkgoRecover(); _ = mgr.Start(ctx) }()
})

var _ = AfterSuite(func() {
    cancel()
    _ = env.Stop(context.Background())
})
```

### With envtest (no changes needed)

Keep kubebuilder's scaffolded `suite_test.go` as-is — it already sets up `envtest.Environment`.

## Controller Tests

Keep the existing `*_controller_test.go` Ginkgo `Describe`/`Context`/`It` blocks unchanged. They use `k8sClient` which is the same `client.Client` interface regardless of the test environment.

If using gomega-matchers (optional with Ginkgo), JQ assertions work inside Ginkgo blocks:

```go
var _ = Describe("Widget Controller", func() {
    It("should update status conditions", func() {
        k := k8sm.New(k8sClient, scheme)

        widget := &appsv1.Widget{ /* ... */ }
        Expect(k8sClient.Create(ctx, widget)).To(Succeed())

        Eventually(k.Get(widget)).Should(
            jq.Match(`.status.conditions[] | select(.type == "Available") | .status == "True"`),
        )
    })
})
```

## Webhooks with k3senvtest

Add webhook manifests and port to the environment setup in `BeforeSuite`:

```go
env, err = k3senv.New(
    k3senv.WithManifests("../../config/crd/bases", "../../config/webhook"),
    k3senv.WithScheme(scheme),
    k3senv.WithWebhookPort(9443),
    k3senv.WithAutoInstallWebhooks(true),
)
```
