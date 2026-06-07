# API Design

## Spec and Status Conventions

**SHOULD** follow the Kubernetes spec/status contract: `spec` holds desired state, `status` holds observed state. Status must not contain desired-state fields. Spec must not contain observed-state fields.

**SHOULD** enable the status subresource when a `Status` field exists on the root type:

```go
// +kubebuilder:subresource:status
```

## Resource Scope

**CONSIDER** setting `+kubebuilder:resource:scope=` explicitly on all root types. The default is `Namespaced`.

```go
// +kubebuilder:resource:scope=Namespaced
// +kubebuilder:resource:scope=Cluster
```

Cluster-scoped resources generate ClusterRole RBAC, cannot use `client.InNamespace()`, and have no namespace isolation in tests.

## Optional and Required Fields

**SHOULD** mark optional fields with both `+optional` and `omitempty` in the JSON tag:

```go
// +optional
Description string `json:"description,omitempty"`
```

**SHOULD** mark required fields with explicit validation:

```go
// +kubebuilder:validation:Required
Name string `json:"name"`
```

## Numeric Types

**CONSIDER** using signed integer types (`int32`, `int64`) for CRD fields. Unsigned types (`uint`, `uint32`, `uint64`) are not representable in JSON Schema.

## Enums

**SHOULD** use string-typed CamelCase values for enum fields:

```go
// +kubebuilder:validation:Enum=Running;Paused;Stopped
Phase string `json:"phase"`
```

## Printer Columns

**CONSIDER** defining `+kubebuilder:printcolumn` on root types for useful `kubectl get` output:

```go
// +kubebuilder:printcolumn:name="Phase",type=string,JSONPath=`.status.phase`
// +kubebuilder:printcolumn:name="Age",type=date,JSONPath=`.metadata.creationTimestamp`
```

## ObservedGeneration in Status

**SHOULD** include an `ObservedGeneration int64` field in the status struct so consumers can tell which spec generation the controller last processed:

```go
type WidgetStatus struct {
    ObservedGeneration int64              `json:"observedGeneration,omitempty"`
    Conditions         []metav1.Condition `json:"conditions,omitempty"`
}
```

## List Type Semantics

**SHOULD** add `+listType` markers to all struct-element slice fields. Without them, Server-Side Apply and strategic merge patch have undefined merge behavior.

```go
// +listType=map
// +listMapKey=name
Containers []Container `json:"containers"`

// +listType=set
Ports []int32 `json:"ports"`

// +listType=atomic
Args []string `json:"args"`
```

**MUST** add `+listMapKey` when using `+listType=map`. Without it, SSA cannot identify individual list elements for merge.

## Marker Correctness

**MUST** use valid, correctly spelled marker names. Invalid markers are silently ignored by `controller-gen`.

**SHOULD** match marker types to field types. Do not apply `+kubebuilder:validation:Minimum` to a string field or `+kubebuilder:validation:MinLength` to an integer.

**SHOULD** ensure `+kubebuilder:validation:Enum` values match declared Go constants for the type.

**SHOULD** verify nested `+kubebuilder:default` markers are reachable — a default on a nested field is unreachable if the parent is optional without a default.

**SHOULD** mark all root types with `+kubebuilder:object:root=true`.
