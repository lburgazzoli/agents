# Workload Disruption

These rules apply to controllers that manage workload resources (Deployments, StatefulSets, Jobs, Pods) on behalf of users. Controllers that only manage infrastructure resources (CRDs, webhook configs, operator pods) are not in scope.

## Config Source Traceability

**SHOULD** make every configuration source (env vars, ConfigMaps, CRD spec fields) traceable to the workload spec fields it affects. A reader should be able to determine which config changes affect which workloads without deep code reading.

## Spec Construction

**SHOULD** prefer targeted patches over full spec replacement when updating managed workloads. Full spec replacement on every reconcile triggers a rolling update regardless of whether inputs changed.

When using `CreateOrUpdate`, scope the `MutateFn` to set only fields that changed. A `MutateFn` that sets all fields unconditionally causes rolling updates on any config change.

## ConfigMap and Secret Change Propagation

**SHOULD** avoid hash annotations on workload pod templates that force rolling restarts when ConfigMap or Secret content changes. If the controller watches ConfigMaps/Secrets and propagates changes via hash annotations, every ConfigMap edit triggers a rolling restart of all managed workloads.

Prefer mechanisms that affect only newly created resources, or implement anti-disruption patterns.

## Image Reference Propagation

**SHOULD** gate image reference changes to prevent unconditional rolling updates of all managed workloads. Image changes via env vars, ConfigMaps, or operator upgrades should not cascade to running workloads without explicit gates.

## Anti-Disruption Mechanisms

**SHOULD** implement at least one anti-disruption mechanism when the controller propagates config changes to workload specs:

- **Versioned config pinning** — store config references in Status or annotations so existing resources keep references to old config versions
- **Conditional gates** — skip config propagation to existing resources based on annotations, feature flags, or deployment mode
- **Webhook-only injection** — inject config at pod creation time via mutating admission webhook (new pods only, no rolling update)
- **Annotation-based change detection** — update workload spec only when a trigger annotation changes, not on every reconciliation

## Scope and Blast Radius

**SHOULD** document the disruption scope for every config propagation path. It should be clear which resource types, under what conditions, are affected — and whether the disruption applies to existing resources, new resources, or both.
