# Switch Over If Chains

Use a tagless `switch` whenever two or more related conditions are checked in sequence. Never write `if` / `else if` chains or stacks of consecutive `if ... { return }` guards for the same value.

## Validating a call result

The most common case: a call returns a value and an error, and both need checking before the value is usable.

Instead of:

```go
crd, err := definitions.Get(ctx, resources.DataScienceCluster.CRDFQN(), metav1.GetOptions{})
if err != nil {
    return nil, "", fmt.Errorf("reading DataScienceCluster CRD: %w", err)
}
if crd == nil {
    return nil, "", errors.New(msgInvalidStoredVersions)
}
if len(crd.Status.StoredVersions) == 0 {
    return nil, "", errors.New(msgInvalidStoredVersions)
}
if slices.Contains(crd.Status.StoredVersions, "") {
    return nil, "", errors.New(msgInvalidStoredVersions)
}
```

Write:

```go
definitions := target.Client.APIExtensions().ApiextensionsV1().CustomResourceDefinitions()

crd, err := definitions.Get(ctx, resources.DataScienceCluster.CRDFQN(), metav1.GetOptions{})

switch {
case err != nil:
    return nil, "", fmt.Errorf("reading DataScienceCluster CRD: %w", err)
case crd == nil:
    return nil, "", errors.New(msgInvalidStoredVersions)
case len(crd.Status.StoredVersions) == 0:
    return nil, "", errors.New(msgInvalidStoredVersions)
case slices.Contains(crd.Status.StoredVersions, ""):
    return nil, "", errors.New(msgInvalidStoredVersions)
}
```

Cases are evaluated top to bottom and stop at the first match, so `crd.Status` is only dereferenced after `err` and `crd` have been validated.

## Branching on state

The pattern is not limited to early returns. Replace `if` / `else if` / `else` with `switch` and `default`:

```go
err := c.Get(ctx, client.ObjectKeyFromObject(obj), obj)

switch {
case k8serr.IsNotFound(err):
    err = c.Create(ctx, obj)
case err != nil:
    return fmt.Errorf("reading %s: %w", obj.GetName(), err)
default:
    err = c.Update(ctx, obj)
}
```

## Rules

1. **Two or more conditions** — a chain of related checks becomes a `switch`; a lone `if err != nil` stays an `if`
2. **Order cases as guards** — `err != nil` first, then nil checks, then content checks, so later cases can safely dereference what earlier ones validated; put more specific conditions (e.g., `k8serr.IsNotFound(err)`) before general ones (`err != nil`)
3. **One condition per case** — keep each check on its own `case` even when the bodies are identical, rather than joining them with `||` or a comma list
4. **Wrap errors with context** — the `err` case returns `fmt.Errorf("...: %w", err)`, not the bare error
5. **No `fallthrough`** — and add `default` only when there is real fallback logic
6. **Keep `if` where it fits** — when a condition needs its own init statement (`if v, ok := m[k]; ok`) or when statements must run between the checks
