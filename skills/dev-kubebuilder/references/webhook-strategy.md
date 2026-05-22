# Webhook Strategy Reference

Before creating a classic webhook, evaluate lighter alternatives. Choose the simplest approach that meets the requirement.

## Decision Order

### 1. CRD Validation Markers (preferred for CRD field constraints)

Use when: validating field values on your own CRDs (min/max, pattern, enum, required, cross-field checks).

No webhook server, no TLS, no cert-manager. Validation runs in the API server.

**Simple constraints** — use `+kubebuilder:validation:*` markers:

```go
// +kubebuilder:validation:Minimum=1
// +kubebuilder:validation:Maximum=100
Replicas int32 `json:"replicas"`

// +kubebuilder:validation:Enum=Running;Paused;Stopped
Phase string `json:"phase"`

// +kubebuilder:validation:Pattern=`^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`
Name string `json:"name"`
```

**Cross-field validation** — use CEL expressions via `+kubebuilder:validation:XValidation`:

```go
// +kubebuilder:validation:XValidation:rule="self.minReplicas <= self.maxReplicas",message="minReplicas must be <= maxReplicas"
type AutoscalerSpec struct {
    MinReplicas int32 `json:"minReplicas"`
    MaxReplicas int32 `json:"maxReplicas"`
}
```

**Transition rules** — validate old vs new values on update:

```go
// +kubebuilder:validation:XValidation:rule="self.name == oldSelf.name",message="name is immutable"
type WidgetSpec struct {
    Name string `json:"name"`
}
```

See [markers](markers.md) for the full marker catalog.

### 2. ValidatingAdmissionPolicy (for declarative validation without a webhook server)

Use when: validation is declarative, applies to any resource type (including core types), and the cluster runs Kubernetes 1.30+.

No webhook server, no TLS. CEL expressions evaluated in-process by the API server.

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-labels
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps.example.com"]
        apiVersions: ["v1alpha1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["widgets"]
  validations:
    - expression: "has(object.metadata.labels) && 'team' in object.metadata.labels"
      message: "All widgets must have a 'team' label"
    - expression: "object.spec.replicas <= 10"
      message: "Replicas must not exceed 10"
---
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-labels-binding
spec:
  policyName: require-labels
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchLabels:
        environment: production
```

Place these in `config/validatingadmissionpolicy/` and include in kustomization.

### 3. Classic Webhook (last resort)

Use when: you need mutation/defaulting, conversion between API versions, external state lookups, or cross-resource validation that CEL cannot express.

**Always scope classic webhooks:**

**Namespace selector** — only intercept resources in labeled namespaces:

```go
// +kubebuilder:webhook:path=/validate-...,mutating=false,...,namespaceSelector={"matchLabels":{"managed-by":"my-operator"}}
```

Or configure in the webhook manifest:

```yaml
namespaceSelector:
  matchLabels:
    managed-by: my-operator
```

**Object selector** — only intercept resources with specific labels:

```yaml
objectSelector:
  matchLabels:
    app.kubernetes.io/managed-by: my-operator
```

**Avoid intercepting core types cluster-wide.** If your webhook must intercept pods, deployments, or other core types, always use namespace or object selectors to limit the blast radius. An unscoped webhook on core types can block the entire cluster if the webhook server is down.

**Set `failurePolicy` deliberately:**
- `Fail` — reject the request if the webhook is unreachable (safe for your own CRDs)
- `Ignore` — allow the request through if the webhook is unreachable (safer for core types)

## When You Must Use a Classic Webhook

| Need | Why CEL/markers aren't enough |
|------|-------------------------------|
| Mutation / defaulting | CEL and markers are read-only — they validate but cannot modify |
| Conversion between API versions | Requires Go code to transform between hub and spoke types |
| External state lookup | CEL has no network access — cannot query databases, APIs, or other resources |
| Cross-resource validation | CEL operates on a single object — cannot check relationships between resources |
| Complex business logic | CEL expression complexity has limits — deeply nested logic is unreadable |
