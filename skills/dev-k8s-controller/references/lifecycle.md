# Lifecycle

## Leader Election

**MUST** enable leader election for controllers that run with multiple replicas. Without it, multiple replicas reconcile concurrently causing split-brain.

```go
mgr, err := ctrl.NewManager(cfg, ctrl.Options{
    LeaderElection:                true,
    LeaderElectionID:              "widget-controller.example.com",
    LeaderElectionReleaseOnCancel: true,
})
```

Exceptions: single-replica controllers that explicitly document this, DaemonSet controllers (inherently single-instance per node).

**SHOULD** set `LeaderElectionID` to a unique value. The default may conflict with other controllers in the same namespace.

**SHOULD** use the Lease resource lock (controller-runtime default). ConfigMap and Endpoints locks are deprecated.

**CONSIDER** setting `LeaderElectionReleaseOnCancel: true` for fast failover during graceful shutdown. Without it, the full lease duration must expire before another replica takes over.

## Graceful Shutdown

**SHOULD** use `ctrl.SetupSignalHandler()` and pass its context to `mgr.Start()`. This handles SIGTERM for graceful shutdown.

```go
ctx := ctrl.SetupSignalHandler()
if err := mgr.Start(ctx); err != nil {
    setupLog.Error(err, "unable to start manager")
    os.Exit(1)
}
```

**CONSIDER** configuring `GracefulShutdownTimeout` when the controller has long-running operations or external API calls. The default may not be appropriate.

## Webhook Certificate Provisioning

**SHOULD** make certificate provisioning visible when admission webhooks are configured. Use one of:
- cert-manager annotations on the webhook configuration
- controller-runtime `webhook.Server` CertDir configuration
- OLM annotations

Never leave webhook certificate provisioning undocumented — it is a common source of deployment failures.
