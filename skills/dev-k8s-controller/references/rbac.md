# RBAC

## Marker Placement

**SHOULD** place RBAC markers on the reconciler's `Reconcile` method, not on types.

```go
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets/finalizers,verbs=update
func (r *WidgetReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
```

## Marker-to-Usage Alignment

**SHOULD** audit RBAC markers against actual API calls. Every marker should correspond to a real client call in the controller. Every client call should have a corresponding marker.

Excess permissions that are never used violate least privilege. Missing permissions cause runtime failures.

## No Wildcards

**SHOULD** never use `*` for verbs or resources in RBAC markers. Always list explicit verbs and resource names.

```go
// Bad:
// +kubebuilder:rbac:groups=apps.example.com,resources=*,verbs=*

// Good:
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets,verbs=get;list;watch
```

## Event Permissions

**CONSIDER** aligning event RBAC with event usage. If the controller emits events via an event recorder, add RBAC for events. If it does not emit events, remove event RBAC.

```go
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
```

## Cluster-Scope Justification

**SHOULD** use ClusterRole only when the controller manages cluster-scoped resources. For namespace-scoped operations, prefer Role (set `namespace` in the marker).

```go
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets,verbs=get;list;watch,namespace=system
```
