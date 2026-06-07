# Kubebuilder Patterns Reference

For controller implementation patterns (owner references, status conditions, finalizers, reconciliation, RBAC, error handling), see the `dev-k8s-controller` skill.

## Field Indexing

Index owned resources by owner for efficient lookups.

```go
const ownerKey = ".metadata.controller"

func (r *WidgetReconciler) SetupWithManager(mgr ctrl.Manager) error {
    if err := mgr.GetFieldIndexer().IndexField(
        context.Background(),
        &appsv1.Deployment{},
        ownerKey,
        func(obj client.Object) []string {
            owner := metav1.GetControllerOf(obj)
            if owner == nil || owner.Kind != "Widget" {
                return nil
            }
            return []string{owner.Name}
        },
    ); err != nil {
        return err
    }

    return ctrl.NewControllerManagedBy(mgr).
        For(&appsv1.Widget{}).
        Owns(&appsv1.Deployment{}).
        Complete(r)
}
```

Use in reconciliation:

```go
var children appsv1.DeploymentList
if err := r.List(ctx, &children,
    client.InNamespace(req.Namespace),
    client.MatchingFields{ownerKey: req.Name},
); err != nil {
    return ctrl.Result{}, err
}
```

## Watching External Types

For watching CRDs from other operators (e.g., cert-manager Certificates):

1. Import and register external types in your scheme:

```go
import certmanagerv1 "github.com/cert-manager/cert-manager/pkg/apis/certmanager/v1"

func init() {
    utilruntime.Must(certmanagerv1.AddToScheme(scheme))
}
```

2. Watch with a custom handler:

```go
func (r *WidgetReconciler) SetupWithManager(mgr ctrl.Manager) error {
    return ctrl.NewControllerManagedBy(mgr).
        For(&appsv1.Widget{}).
        Watches(
            &certmanagerv1.Certificate{},
            handler.EnqueueRequestForOwner(
                mgr.GetScheme(), mgr.GetRESTMapper(),
                &appsv1.Widget{}, handler.OnlyControllerOwner(),
            ),
        ).
        Complete(r)
}
```

3. RBAC for external resources:

```go
// +kubebuilder:rbac:groups=cert-manager.io,resources=certificates,verbs=get;list;watch;create;update;patch;delete
```

## Multigroup Directory Layout

### Single-Group (default)

```
api/
  v1/
    widget_types.go
    gadget_types.go
    groupversion_info.go
internal/
  controller/
    widget_controller.go
    gadget_controller.go
    suite_test.go
  webhook/
    v1/
      widget_webhook.go
```

### Multi-Group (`--multigroup`)

```
api/
  apps/
    v1/
      widget_types.go
      groupversion_info.go
  infra/
    v1alpha1/
      machine_types.go
      groupversion_info.go
internal/
  controller/
    apps/
      widget_controller.go
      suite_test.go
    infra/
      machine_controller.go
      suite_test.go
  webhook/
    apps/
      v1/
        widget_webhook.go
    infra/
      v1alpha1/
        machine_webhook.go
```

### Import Paths

Single-group: `<module>/api/v1`
Multi-group: `<module>/api/<group>/v1`

```go
appsv1 "github.com/myorg/myop/api/apps/v1"
infrav1alpha1 "github.com/myorg/myop/api/infra/v1alpha1"
```
