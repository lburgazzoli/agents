# Webhooks

## Webhook Configuration

**SHOULD** set `failurePolicy` explicitly on all webhook configurations. Do not rely on the server default.

- `Fail` — reject if webhook is unreachable (safe for your own CRDs)
- `Ignore` — allow through if unreachable (safer for core types)

**SHOULD** set `sideEffects` explicitly. Use `None` unless the webhook creates side effects.

**CONSIDER** setting `timeoutSeconds` explicitly. The server default may not match your webhook's performance characteristics.

## Match Scope

**SHOULD** scope webhooks narrowly with namespace or object selectors. Never intercept core types (pods, deployments) cluster-wide — an unscoped webhook on core types blocks the entire cluster if the webhook server is down.

```yaml
namespaceSelector:
  matchLabels:
    managed-by: my-operator
```

## No Long-Running Admission Logic

**SHOULD** keep admission handlers fast and self-contained. Do not perform external service calls, database queries, or long-running operations in webhook handlers.

## CEL over Webhooks

**CONSIDER** using CEL validation rules for simple constraints before creating a validating webhook. CEL runs in the API server with no webhook round-trip.

Use webhooks only when you need:
- Mutation / defaulting (CEL is read-only)
- Conversion between API versions
- External state lookups
- Cross-resource validation
- Complex business logic beyond CEL expression limits

## CEL Transition Rules

**SHOULD** complement CEL transition rules (using `oldSelf`) with non-transition validation for the CREATE path. Transition rules only fire on UPDATE — without a separate rule, the CREATE path is unvalidated.

```go
// Immutability enforcement — fires on UPDATE only
// +kubebuilder:validation:XValidation:rule="self.name == oldSelf.name",message="name is immutable"

// Also add CREATE-path validation if needed
// +kubebuilder:validation:XValidation:rule="self.name.size() > 0",message="name must not be empty"
```

## Field Immutability

**SHOULD** enforce immutable fields via CEL transition rules or validating webhooks. If a field is treated as immutable by the controller, it must be enforced at the API level.

```go
// +kubebuilder:validation:XValidation:rule="self == oldSelf",message="spec is immutable"
```

## Idempotent Defaulting

**SHOULD** guard `Default()` with nil/zero checks before applying defaults. Applying defaults twice must produce the same result.

```go
func (r *Widget) Default() {
    if r.Spec.Replicas == nil {
        r.Spec.Replicas = ptr.To(int32(1))
    }
}
```

## Schema and Webhook Consistency

**SHOULD** ensure `+kubebuilder:default` markers and `Default()` webhook agree on values. Conflicting defaults create order-dependent behavior.

## User-Owned Fields

**SHOULD** not unconditionally set spec fields that users control. This causes SSA field ownership conflicts where the webhook field manager competes with the user.

## Reinvocation Policy

**CONSIDER** setting `reinvocationPolicy` on mutating webhooks. Without it, mutations may be overwritten by later webhooks without re-evaluation.

## CEL Cost Safety

**MUST** bound collection sizes with `+kubebuilder:validation:MaxItems` or `+kubebuilder:validation:MaxProperties` before using CEL rules that iterate over collections. Unbounded collections cause the API server to reject the CRD at registration.

**SHOULD** guard optional fields with `has()` in CEL expressions. Accessing a nil optional field without a guard causes CEL evaluation failures.
