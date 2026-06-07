# API Versioning Reference

## Version Progression

| Version | Stability | Expectations |
|---------|-----------|-------------|
| `v1alpha1` | Experimental | Breaking changes expected. May be removed without notice. |
| `v1beta1` | Feature-complete | API shape mostly stable. Minor breaking changes possible with migration. |
| `v1` | Stable | No breaking changes within the major version. Only additive changes. |

Start with `v1alpha1`. Promote when the API shape stabilizes.

## Hub and Spoke Model

One version is the **hub** (canonical storage format). All others are **spokes** that convert through the hub. This reduces conversion functions from O(n^2) to O(n).

### Designate the Hub

The hub is the storage version — usually the most stable version.

```go
// In api/<group>/v1/widget_conversion.go

// Hub marks this version as the hub for conversion.
func (*Widget) Hub() {}
```

Mark with `+kubebuilder:storageversion` on the root type:

```go
// +kubebuilder:object:root=true
// +kubebuilder:storageversion
type Widget struct { ... }
```

### Implement Spoke Conversion

Each spoke implements `ConvertTo()` (spoke → hub) and `ConvertFrom()` (hub → spoke).

```go
// In api/<group>/v2/widget_conversion.go

import (
    "sigs.k8s.io/controller-runtime/pkg/conversion"
    v1 "github.com/myorg/myop/api/apps/v1"
)

func (src *Widget) ConvertTo(dstRaw conversion.Hub) error {
    dst := dstRaw.(*v1.Widget)
    dst.ObjectMeta = src.ObjectMeta
    dst.Spec.Name = src.Spec.DisplayName
    dst.Status = v1.WidgetStatus(src.Status)
    return nil
}

func (dst *Widget) ConvertFrom(srcRaw conversion.Hub) error {
    src := srcRaw.(*v1.Widget)
    dst.ObjectMeta = src.ObjectMeta
    dst.Spec.DisplayName = src.Spec.Name
    dst.Status = WidgetStatus(src.Status)
    return nil
}
```

### Round-Trip Fidelity

Converting hub → spoke → hub must preserve all data. If a spoke version lacks a field that the hub has, store it in annotations:

```go
func (src *Widget) ConvertTo(dstRaw conversion.Hub) error {
    dst := dstRaw.(*v1.Widget)
    dst.ObjectMeta = src.ObjectMeta
    // Restore field from annotation if it was preserved
    if val, ok := dst.Annotations["apps.example.com/priority"]; ok {
        dst.Spec.Priority = parseInt(val)
        delete(dst.Annotations, "apps.example.com/priority")
    }
    return nil
}

func (dst *Widget) ConvertFrom(srcRaw conversion.Hub) error {
    src := srcRaw.(*v1.Widget)
    dst.ObjectMeta = src.ObjectMeta
    // Preserve field in annotation that this version doesn't have
    if dst.Annotations == nil {
        dst.Annotations = map[string]string{}
    }
    dst.Annotations["apps.example.com/priority"] = fmt.Sprintf("%d", src.Spec.Priority)
    return nil
}
```

### Multi-Spoke Setup (3+ Versions)

All spokes convert through the hub. No direct spoke-to-spoke conversion.

```
v1alpha1 (spoke) ←→ v1 (hub) ←→ v2 (spoke)
```

Each spoke independently implements `ConvertTo`/`ConvertFrom` targeting the hub. The conversion webhook routes automatically.

### Creating the Conversion Webhook

```bash
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create webhook --group apps --version v1 --kind Widget \
  --conversion --spoke v2

# For additional spokes:
go run sigs.k8s.io/kubebuilder/v4/cmd@latest create webhook --group apps --version v1 --kind Widget \
  --conversion --spoke v1alpha1
```

## Deprecation

Mark old versions with a deprecation warning:

```go
// +kubebuilder:object:root=true
// +kubebuilder:deprecatedversion:warning="v1alpha1 is deprecated; use v1beta1"
type Widget struct { ... }
```

To stop serving entirely:

```go
// +kubebuilder:unservedversion
type Widget struct { ... }
```

## Kustomize Config for Conversion

In `config/crd/kustomization.yaml`, uncomment:

```yaml
patches:
- path: patches/webhook_in_<group>_<kind>.yaml
- path: patches/cainjection_in_<group>_<kind>.yaml
```

In `config/default/kustomization.yaml`, enable:

```yaml
resources:
- ../certmanager
- ../webhook
```
