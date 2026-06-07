# Standard envtest Environment Reference

Uses `sigs.k8s.io/controller-runtime/pkg/envtest` — runs an in-process kube-apiserver and etcd. No container runtime required.

## Makefile

Convert `setup-envtest` to `go run` style (Step 9 handles the rest):

```makefile
SETUP_ENVTEST_VERSION ?= <pinned version>
SETUP_ENVTEST = go run sigs.k8s.io/controller-runtime/tools/setup-envtest@$(SETUP_ENVTEST_VERSION)

.PHONY: test
test: manifests generate fmt ## Run tests
	KUBEBUILDER_ASSETS="$$($(SETUP_ENVTEST) use $(ENVTEST_K8S_VERSION) --bin-dir $(LOCALBIN) -p path)" go test -race -count=1 ./...
```

## Limitations

- **No garbage collection** — owner references exist but cascading deletes do not happen. Test owner reference existence instead.
- **No namespace deletion** — namespaces stay in Terminating state. Use unique namespaces per test.
- **No built-in controllers** — Deployment, ReplicaSet, etc. are absent. Only your controllers run.
- **Webhook testing** — requires manual cert setup via `WebhookInstallOptions`.
- **CRD paths** — multigroup projects need correct relative path with extra `..` segments.
