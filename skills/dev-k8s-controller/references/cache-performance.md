# Cache and Performance

## Cached Reads

**CONSIDER** using the cached client for watched resources. Reserve direct API reads for consistency-critical paths where stale cache data is unacceptable.

## Status Update Efficiency

**CONSIDER** guarding status updates with a comparison. Skip the status update when no fields changed to avoid unnecessary API server writes.

## SSA Coherence

**SHOULD** use a consistent field manager when using Server-Side Apply. Do not mix SSA with non-SSA updates (Update/Patch) on the same fields — this creates field ownership conflicts.

## Render Gating

**CONSIDER** gating Helm or Kustomize rendering in the reconcile loop. Fresh renders on every reconcile iteration waste resources when inputs have not changed.

Gate rendering by generation, content hash, or resource version to skip unchanged work.

## Watch Predicates

**CONSIDER** adding predicates to watches to reduce reconcile churn. Without predicates, every update to a watched resource triggers reconciliation — including status-only updates and metadata changes.

```go
ctrl.NewControllerManagedBy(mgr).
    For(&appsv1.Widget{}).
    Watches(&corev1.ConfigMap{},
        handler.EnqueueRequestForOwner(mgr.GetScheme(), mgr.GetRESTMapper(), &appsv1.Widget{}),
        builder.WithPredicates(predicate.ResourceVersionChangedPredicate{}),
    ).
    Complete(r)
```

## Hidden Informers

**CONSIDER** routing all watches through the manager cache. Creating additional informers or list/watches outside the manager cache duplicates API server load and bypasses cache filters.

## Cache-Watch Alignment

**SHOULD** read from cache only for resources the controller watches. Reading a cached value for an unwatched resource returns stale data — the informer is never populated.

**SHOULD** use one informer type per resource. Mixing typed and unstructured informers for the same GVK creates duplicate cache entries.

## Cache Filters

**SHOULD** configure label, field, or namespace selectors on watched types. Without filters, informers are cluster-wide.

This is critical for high-cardinality types (Secret, ConfigMap, Pod) — cluster-wide informers for these types risk OOM.

```go
mgr, err := ctrl.NewManager(cfg, ctrl.Options{
    Cache: cache.Options{
        ByObject: map[client.Object]cache.ByObject{
            &corev1.Secret{}: {
                Label: labels.SelectorFromSet(labels.Set{
                    "managed-by": "my-operator",
                }),
            },
        },
    },
})
```

## Implicit Informers

**SHOULD** avoid `client.Get` or `client.List` for types not in the watch set. The cached client silently creates a cluster-wide informer for unwatched types, bypassing cache filters. This is especially dangerous for Secret, ConfigMap, and Pod.

## Memory Configuration

**SHOULD** set `GOMEMLIMIT` to 80-90% of the container memory limit in the deployment manifest. Without it, Go's GC cannot pressure-tune to the container's memory constraint.

**CONSIDER** configuring `DefaultTransform` to strip `managedFields` from cached objects. Managed fields are large and rarely needed by controllers.
