# Status Conditions

## Condition Types

Define standard condition types as constants. Use `meta.SetStatusCondition()` for updates.

```go
import "k8s.io/apimachinery/pkg/api/meta"

const (
    ConditionAvailable   = "Available"
    ConditionProgressing = "Progressing"
    ConditionDegraded    = "Degraded"
)
```

## Status Type Pattern

Always include `Conditions []metav1.Condition` in your status struct.

```go
type WidgetStatus struct {
    Conditions         []metav1.Condition `json:"conditions,omitempty"`
    ObservedGeneration int64              `json:"observedGeneration,omitempty"`
    Phase              string             `json:"phase,omitempty"`
}
```

## Consistent Condition Updates

**SHOULD** set or preserve all condition types on every reconcile exit path. If a reconcile path updates status but only sets a subset of condition types, the omitted conditions retain stale values from a previous reconcile.

```go
meta.SetStatusCondition(&widget.Status.Conditions, metav1.Condition{
    Type:               ConditionAvailable,
    Status:             metav1.ConditionTrue,
    Reason:             "ReconcileSuccess",
    Message:            "All child resources are ready",
    ObservedGeneration: widget.Generation,
    LastTransitionTime: metav1.Now(),
})

if err := r.Status().Update(ctx, widget); err != nil {
    return ctrl.Result{}, err
}
```

## ObservedGeneration

**SHOULD** set `ObservedGeneration: obj.Generation` on every condition write when using `metav1.Condition`. This tells consumers which spec generation the controller last processed.

## Status Overwrite Prevention

**CONSIDER** scoping status writes to controller-owned fields only. When multiple controllers share the status subresource, use targeted patches or SSA to avoid overwriting fields managed by another controller.

## Consistent Conflict Handling

**CONSIDER** using the same conflict handling strategy across all status update sites. If some sites use `RetryOnConflict` while others write directly, the conflict resilience is inconsistent.

Sites in error paths that return the error (triggering controller-runtime requeue) are acceptable without explicit retry.

Do not create a finding for the mere absence of `RetryOnConflict`. Do not list `RetryOnConflict` as a positive highlight.
