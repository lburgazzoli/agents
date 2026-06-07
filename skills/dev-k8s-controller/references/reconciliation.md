# Reconciliation

## Idempotent Reconcile Paths

**SHOULD** check current state before writes. Use create-or-update, Server-Side Apply, or field-by-field comparison. Never create, update, or delete resources unconditionally.

```go
result, err := ctrl.CreateOrUpdate(ctx, r.Client, child, func() error {
    child.Spec = desiredSpec
    return ctrl.SetControllerReference(owner, child, r.Scheme)
})
```

**SHOULD** skip writes when nothing changed. Short-circuit on no-op reconciles to avoid unnecessary API server load.

## Not-Found Handling

**SHOULD** return cleanly when the primary resource is not found — it was deleted.

```go
obj := &appsv1.Widget{}
if err := r.Get(ctx, req.NamespacedName, obj); err != nil {
    return ctrl.Result{}, client.IgnoreNotFound(err)
}
```

Never requeue on not-found. Never log not-found as an error.

## Error Handling and Requeue Strategy

**SHOULD** return transient errors so the controller requeues with exponential backoff. Do not swallow errors with logging only.

```go
if err := r.Create(ctx, child); err != nil {
    return ctrl.Result{}, err
}
```

**CONSIDER** using `RequeueAfter` with an explicit duration for time-based scheduling. Bare `Requeue: true` without a duration causes tight-loop reconciliation.

```go
return ctrl.Result{RequeueAfter: 30 * time.Second}, nil
```

**SHOULD** surface permanent errors via status conditions rather than returning them for infinite requeue. A terminal condition tells the user what is wrong without filling the logs.

## Spec-Status Contract

**SHOULD** write only to the status subresource and metadata (labels, annotations, finalizers) on the primary resource. The controller must never issue Update or Patch calls targeting the primary resource's spec — spec is user-owned.

## Concurrency Safety

**SHOULD** protect mutable reconciler struct fields when `MaxConcurrentReconciles > 1`. Use `sync.Mutex`, `sync.RWMutex`, `sync.Map`, or `atomic` operations.

Immutable fields are safe without synchronization: `client.Client`, `logr.Logger`, `*runtime.Scheme`, `record.EventRecorder`.

## Reconcile Step Ordering

**SHOULD** reconcile dependencies before dependents. Create ServiceAccount and RBAC before Deployment. Create ConfigMap and Secret before workloads that mount them.

**CONSIDER** adding conditional guards for optional components. Steps that handle optional features or deletion-specific logic should not run unconditionally.

**CONSIDER** short-circuiting unchanged sub-resources. When the total number of reconcile steps is large, use generation-based gating or content-hash comparison to skip sub-resources that have not changed.
