# Production Readiness

## Test Coverage

**SHOULD** write unit or table-driven tests for reconcile logic covering the happy path, error paths, and at least one of: idempotency, finalizer lifecycle, or status transitions.

**SHOULD** write integration tests with envtest (or k3s-envtest) when the project uses controller-runtime patterns extensively.

**CONSIDER** avoiding sleep-based or timing-fragile tests. Use `Eventually` / `Consistently` from Gomega or polling patterns instead of fixed sleeps.

## Structured Logging

**SHOULD** use controller-runtime's logger or `klog` for structured logging. Never use `fmt.Printf`, `log.Println`, or other unstructured logging in production controller code.

## Events

**CONSIDER** emitting events only on meaningful state transitions — not on every reconcile iteration. Events on every reconcile flood the event stream without adding value.

## Metrics

**CONSIDER** adding custom Prometheus metrics for reconcile duration or business-critical controller behavior — external service calls, rendering operations, data pipeline stages.

Simple reconcile loops may rely on controller-runtime's built-in metrics. Custom metrics add value when the controller has specific code paths worth monitoring.

## Resource Requests and Limits

**SHOULD** define resource requests and limits in the manager deployment manifest.

## Security Context

**SHOULD** set a restrictive security context on the manager deployment:

```yaml
securityContext:
  runAsNonRoot: true
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  seccompProfile:
    type: RuntimeDefault
  capabilities:
    drop:
      - ALL
```

## Health Probes

**SHOULD** configure liveness and readiness probes matching the manager's health endpoint configuration.

## Network Policy

**CONSIDER** defining a NetworkPolicy when the controller targets hardened or multi-tenant environments.

## Implicit Informer OOM Risk

**SHOULD** avoid `client.Get` or `client.List` for high-cardinality types (Secret, ConfigMap, Pod) that are not in the watch set. The cached client silently creates cluster-wide informers for these types, bypassing cache filters and risking OOM.

## External Service Resilience

**SHOULD** add retry/backoff, timeouts, or circuit breakers when the controller connects to external services (databases, caches, message queues, external APIs). Without resilience patterns, a single external service failure can block all reconciliation.
