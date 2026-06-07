# Kubebuilder Markers Reference

Markers are Go comments that `controller-gen` reads to generate CRDs, RBAC, and webhook configs. Run `make manifests` after changing any marker.

## CRD Type Markers

Place on the root CRD struct (the one with `metav1.TypeMeta` and `metav1.ObjectMeta`).

| Marker | Purpose |
|--------|---------|
| `+kubebuilder:object:root=true` | Marks the root CRD object (auto-generated) |
| `+kubebuilder:subresource:status` | Enables `/status` subresource |
| `+kubebuilder:subresource:scale:specpath=.spec.replicas,statuspath=.status.replicas,selectorpath=.status.selector` | Enables `/scale` subresource |
| `+kubebuilder:storageversion` | Designates this version as the etcd storage version (exactly one per kind) |
| `+kubebuilder:unservedversion` | Stops serving this version via the API |
| `+kubebuilder:skipversion` | Removes version from CRD spec entirely |
| `+kubebuilder:deprecatedversion:warning="Use v1beta1 instead"` | Marks version deprecated with warning |
| `+kubebuilder:metadata:annotations="key=value"` | Adds annotations to the CRD object |
| `+kubebuilder:metadata:labels="key=value"` | Adds labels to the CRD object |

## Resource Configuration

Place on the root CRD struct.

```go
// +kubebuilder:resource:path=widgets,scope=Namespaced,shortName=wg,categories=all,singular=widget
```

| Parameter | Values | Default |
|-----------|--------|---------|
| `scope` | `Namespaced`, `Cluster` | `Namespaced` |
| `path` | Plural resource name | Auto from kind |
| `shortName` | Alias for `kubectl get <short>` | None |
| `categories` | Groups (e.g., `all`) | None |
| `singular` | Singular name override | Auto from kind |

### Cluster-Scoped Resources

```go
// +kubebuilder:resource:scope=Cluster
type ClusterWidget struct { ... }
```

Implications:
- RBAC generates `ClusterRole` (not `Role`)
- `ObjectMeta.Namespace` must not be set
- `client.InNamespace()` cannot be used in queries
- No namespace isolation between tests

## Print Columns

Place on the root CRD struct. Adds columns to `kubectl get` output.

```go
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`
// +kubebuilder:printcolumn:name="Replicas",type=integer,JSONPath=`.spec.replicas`,priority=1
```

| Parameter | Values |
|-----------|--------|
| `type` | `string`, `integer`, `number`, `boolean`, `date` |
| `JSONPath` | JSONPath expression to the field |
| `priority` | `0` = always shown, `1` = shown with `-o wide` |

## Validation Markers

Place on struct fields in Spec/Status types.

### Required / Optional

```go
// +kubebuilder:validation:Required
Name string `json:"name"`

// +optional
Description string `json:"description,omitempty"`
```

### Numeric Constraints

```go
// +kubebuilder:validation:Minimum=1
// +kubebuilder:validation:Maximum=100
// +kubebuilder:validation:MultipleOf=5
Replicas int32 `json:"replicas"`
```

### String Constraints

```go
// +kubebuilder:validation:MinLength=1
// +kubebuilder:validation:MaxLength=253
// +kubebuilder:validation:Pattern=`^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`
Name string `json:"name"`
```

### Enums

```go
// +kubebuilder:validation:Enum=Running;Paused;Stopped
Phase string `json:"phase"`
```

### Default Values

```go
// +kubebuilder:default:=3
Replicas *int32 `json:"replicas,omitempty"`

// +kubebuilder:default:="Running"
Phase string `json:"phase,omitempty"`
```

### List Constraints

```go
// +kubebuilder:validation:MinItems=1
// +kubebuilder:validation:MaxItems=10
// +kubebuilder:validation:UniqueItems=true
Ports []int32 `json:"ports"`
```

Array item validation uses `items:` prefix:

```go
// +kubebuilder:validation:items:MinLength=1
Names []string `json:"names"`
```

### CEL Validation (XValidation)

```go
// +kubebuilder:validation:XValidation:rule="self.minReplicas <= self.maxReplicas",message="minReplicas must be <= maxReplicas"
type AutoscalerSpec struct {
    MinReplicas int32 `json:"minReplicas"`
    MaxReplicas int32 `json:"maxReplicas"`
}
```

### Union / Discriminator Markers

```go
// +kubebuilder:validation:ExactlyOneOf=InlineConfig;ConfigMapRef
// +kubebuilder:validation:AtLeastOneOf=CPU;Memory
// +kubebuilder:validation:AtMostOneOf=Secret;ConfigMap
```

### Special Type Markers

| Marker | Purpose |
|--------|---------|
| `+kubebuilder:validation:XIntOrString` | IntOrString union type |
| `+kubebuilder:validation:XEmbeddedResource` | Embedded resource with apiVersion/kind/metadata |
| `+kubebuilder:validation:Schemaless` | No schema introspection |

### List Merge Strategy

```go
// +listType=map
// +listMapKey=name
Containers []Container `json:"containers"`

// +listType=set
Ports []int32 `json:"ports"`

// +listType=atomic
Args []string `json:"args"`
```

## RBAC Markers

Place on the reconciler's `Reconcile` method (not on types).

```go
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets,verbs=get;list;watch;create;update;patch;delete
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets/status,verbs=get;update;patch
// +kubebuilder:rbac:groups=apps.example.com,resources=widgets/finalizers,verbs=update
// +kubebuilder:rbac:groups="",resources=events,verbs=create;patch
```

| Parameter | Purpose |
|-----------|---------|
| `groups` | API groups (`""` for core) |
| `resources` | Resource names (plural) |
| `verbs` | `get;list;watch;create;update;patch;delete` |
| `resourceNames` | Restrict to specific resource names |
| `namespace` | If set, generates `Role` instead of `ClusterRole` |

## Webhook Markers

### Mutating (Defaulting) Webhook

```go
// +kubebuilder:webhook:path=/mutate-apps-example-com-v1-widget,mutating=true,failurePolicy=fail,sideEffects=None,groups=apps.example.com,resources=widgets,verbs=create;update,versions=v1,name=mwidget.kb.io,admissionReviewVersions=v1
```

### Validating Webhook

```go
// +kubebuilder:webhook:path=/validate-apps-example-com-v1-widget,mutating=false,failurePolicy=fail,sideEffects=None,groups=apps.example.com,resources=widgets,verbs=create;update,versions=v1,name=vwidget.kb.io,admissionReviewVersions=v1
```

| Parameter | Values |
|-----------|--------|
| `path` | HTTP path for the webhook |
| `mutating` | `true` (defaulting) or `false` (validating) |
| `failurePolicy` | `fail` or `ignore` |
| `sideEffects` | `None`, `Some`, `NoneOnDryRun` |
| `groups` | API groups to intercept |
| `resources` | Resources to intercept (plural) |
| `verbs` | `create;update;delete;connect;*` |
| `versions` | API versions to intercept |
| `name` | Webhook name (domain format) |
| `admissionReviewVersions` | Supported versions (usually `v1`) |

## Group Name Marker

Package-level comment in `groupversion_info.go`:

```go
// +groupName=apps.example.com
package v1
```
