# API Versioning

## Version Progression

| Version | Stability | Expectations |
|---------|-----------|-------------|
| `v1alpha1` | Experimental | Breaking changes expected. May be removed. |
| `v1beta1` | Feature-complete | API shape mostly stable. Minor breaks with migration. |
| `v1` | Stable | No breaking changes within the major version. Additive only. |

Start with `v1alpha1`. Promote when the API shape stabilizes.

## Storage Version

**MUST** mark exactly one version per kind as the storage version:

```go
// +kubebuilder:storageversion
```

The storage version is the canonical format stored in etcd. All other versions convert through it.

## Served and Deprecated Versions

**SHOULD** set served and deprecated flags intentionally. A deprecated version that is still served without migration guidance confuses users.

Mark deprecated versions with a warning:

```go
// +kubebuilder:deprecatedversion:warning="v1alpha1 is deprecated; use v1beta1"
```

## Conversion Strategy

**MUST** use webhook conversion when multiple served versions have schema differences. Using `None` conversion with different schemas silently drops or zeroes fields that differ between versions.

**SHOULD** ensure version evolution is additive. New versions add fields; they do not remove or rename fields without a documented migration path.

## CRD Upgrade Safety

**SHOULD** provide a conversion mechanism when serving multiple CRD versions. Without conversion, the API server performs no field mapping between versions.

**SHOULD** document migration paths for deprecated versions. Deprecated versions that are still served need visible migration documentation or tooling.

**SHOULD** coordinate storage version changes. When changing the storage version, ensure awareness of stored version migration — existing objects in etcd remain in the old storage format until rewritten.

For hub-spoke conversion implementation (ConvertTo/ConvertFrom), see the `dev-k8s-kubebuilder` skill reference on api-versioning.
