# Ownership and Finalizers

## Owner References

**SHOULD** set owner references on all child resources. This enables garbage collection when the owner is deleted and triggers reconciliation when owned resources change.

```go
import "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

if err := ctrl.SetControllerReference(owner, child, r.Scheme); err != nil {
    return ctrl.Result{}, err
}
if err := r.Create(ctx, child); err != nil {
    return ctrl.Result{}, err
}
```

Declare owned types in `SetupWithManager`:

```go
func (r *WidgetReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&appsv1.Widget{}).
        Owns(&corev1.ConfigMap{}).
        Owns(&appsv1.Deployment{}).
        Complete(r)
}
```

## Finalizers

Use finalizers when the controller must clean up external resources on deletion. The pattern has strict ordering requirements.

**MUST** not remove the finalizer before cleanup completes. Removing the finalizer before external cleanup succeeds means the resource is deleted and cleanup never finishes.

**SHOULD** gate external cleanup with a finalizer. If the controller performs external cleanup on deletion but does not use a finalizer, Kubernetes may delete the resource before cleanup runs.

```go
import "sigs.k8s.io/controller-runtime/pkg/controller/controllerutil"

const finalizerName = "apps.example.com/finalizer"

func (r *WidgetReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
    widget := &appsv1.Widget{}
    if err := r.Get(ctx, req.NamespacedName, widget); err != nil {
        return ctrl.Result{}, client.IgnoreNotFound(err)
    }

    if widget.DeletionTimestamp.IsZero() {
        if !controllerutil.ContainsFinalizer(widget, finalizerName) {
            controllerutil.AddFinalizer(widget, finalizerName)
            if err := r.Update(ctx, widget); err != nil {
                return ctrl.Result{}, err
            }
        }
    } else {
        if controllerutil.ContainsFinalizer(widget, finalizerName) {
            if err := r.cleanupExternal(ctx, widget); err != nil {
                return ctrl.Result{}, err
            }
            controllerutil.RemoveFinalizer(widget, finalizerName)
            if err := r.Update(ctx, widget); err != nil {
                return ctrl.Result{}, err
            }
        }
        return ctrl.Result{}, nil
    }

    // Normal reconciliation ...
}
```

RBAC for finalizers:

```go
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets/finalizers,verbs=update
```

## Cleanup Sequencing

Clean up in reverse-dependency order. Delete dependent resources before their dependencies. Ensure all cleanup operations succeed before removing the finalizer.
