---
name: dev-k8s-controller
description: >
  Kubernetes controller implementation best practices for controller-runtime
  projects. Covers reconciliation, error handling, RBAC, status conditions,
  ownership, finalizers, cache, lifecycle, production readiness, and workload
  disruption prevention. Read the relevant reference on demand based on context.
  Triggers on: reconciler, Reconcile, controller-runtime, ctrl.Result, RequeueAfter,
  finalizer, owner reference, status condition, ObservedGeneration, RBAC markers,
  leader election, graceful shutdown, watch predicate, cache filter, workload disruption.
user-invocable: false
---

# Kubernetes Controller Best Practices

Match the task to a topic using the keywords below, then read only that reference.

| Topic | Keywords | Reference |
|-------|----------|-----------|
| Reconciliation | `Reconcile`, idempotent, no-op, not-found, `IsNotFound`, create-or-update, `RequeueAfter`, requeue, transient error, permanent error, backoff, spec-status contract, concurrency, step ordering | [reconciliation](references/reconciliation.md) |
| RBAC | `RBAC`, `+kubebuilder:rbac`, `ClusterRole`, least privilege, wildcard, event permissions | [rbac](references/rbac.md) |
| Status and conditions | status condition, `ObservedGeneration`, `meta.SetStatusCondition`, condition update, status overwrite, conflict handling | [status-conditions](references/status-conditions.md) |
| Ownership and finalizers | owner reference, `SetControllerReference`, finalizer, `controllerutil.AddFinalizer`, cleanup, garbage collection | [ownership-finalizers](references/ownership-finalizers.md) |
| API design | CRD, spec/status, `+optional`, `omitempty`, `+kubebuilder:validation`, printer columns, enum, unsigned, scope, `+listType`, `+listMapKey` | [api-design](references/api-design.md) |
| API versioning | storage version, hub, spoke, conversion, deprecated version, additive evolution, CRD upgrade safety | [api-versioning](references/api-versioning.md) |
| Webhooks | webhook, `failurePolicy`, `sideEffects`, defaulting, CEL, `ValidatingAdmissionPolicy`, transition rule, immutability, `reinvocationPolicy` | [webhooks](references/webhooks.md) |
| Lifecycle | leader election, `LeaderElectionID`, graceful shutdown, signal handler, `SIGTERM`, cert-manager, webhook certificate | [lifecycle](references/lifecycle.md) |
| Cache and performance | cache filter, watch predicate, informer, `GOMEMLIMIT`, `DefaultTransform`, `managedFields`, implicit informer | [cache-performance](references/cache-performance.md) |
| Production readiness | envtest, integration test, structured logging, `klog`, metrics, Prometheus, health probe, resource limits, security context, network policy | [production-readiness](references/production-readiness.md) |
| Workload disruption | rolling restart, config propagation, hash annotation, ConfigMap watch, image reference, anti-disruption, versioned config | [workload-disruption](references/workload-disruption.md) |
| Portability | vendor API, vendor CRD, runtime discovery, build tags, feature gate, platform dependency | [portability](references/portability.md) |

For kubebuilder scaffolding, markers, and project setup, see the `dev-k8s-kubebuilder` skill.
