# Portability

## Vendor API Isolation

**SHOULD** never call vendor-specific APIs (OpenShift, EKS, GKE, AKS) unconditionally. Guard vendor API usage with runtime discovery, build tags, or feature gates.

```go
// Runtime discovery example
_, err := mgr.GetRESTMapper().RESTMapping(
    schema.GroupKind{Group: "route.openshift.io", Kind: "Route"},
)
if err != nil {
    // Route API not available — skip Route reconciliation
    setupLog.Info("Route API not available, skipping Route controller")
} else {
    // Register Route controller
}
```

## Startup Dependencies

**MUST** handle missing vendor CRDs gracefully at startup. The controller must not fail to start on non-vendor platforms due to unguarded CRD or API dependencies.

When a vendor CRD is not installed, the controller should skip the corresponding watch and log a warning — not crash.
