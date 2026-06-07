# k3s-envtest Environment Reference

Uses `github.com/lburgazzoli/k3s-envtest` — runs a real k3s cluster in a container via testcontainers-go.

## Dependencies

```bash
go get github.com/lburgazzoli/k3s-envtest
go get github.com/lburgazzoli/gomega-matchers
```

## Makefile

Remove envtest-related targets from kubebuilder's generated Makefile:
- Remove `ENVTEST` variable and `setup-envtest` binary download
- Remove `KUBEBUILDER_ASSETS` from the `test` target
- Simplify `test` target to: `go test -race -count=1 ./...`

## Webhooks

```go
env, err := k3senv.New(
    k3senv.WithManifests("../../config/crd/bases", "../../config/webhook"),
    k3senv.WithScheme(scheme),
    k3senv.WithWebhookPort(9443),
    k3senv.WithAutoInstallWebhooks(true),
)
```

Use `env.WebhookServer()` to register webhook handlers, and `env.CertificatePaths()` for TLS config.

## Key Differences from Standard envtest

| Feature | Standard envtest | k3s-envtest |
|---------|------------------|-------------|
| Garbage collection | Not available | Works (real k3s) |
| Namespace deletion | Stuck in Terminating | Works |
| Built-in controllers | Absent | Present (real k3s) |
| Webhook TLS | Manual setup | Auto-generated certs |
| Binary downloads | Required (setup-envtest) | None (container image) |
| Container runtime | Not needed | Required (Podman/Docker) |

## Gotchas

- Requires a container runtime — see `dev-testcontainers` skill for Podman setup
- Slower startup than in-process envtest (~10-15s for container spin-up)
- Container networking: webhook host is `host.containers.internal:PORT`
- The k3s image is pulled on first run; CI should cache it
