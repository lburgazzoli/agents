# Making Asynchronous Assertions

Doc: https://onsi.github.io/gomega/#making-asynchronous-assertions

## Eventually

Polls until the matcher passes (default: 1s timeout, 10ms interval).

### Category 1 — raw value (re-fetched each poll via pointer/func)

```go
// Use a function so the value is re-evaluated each poll
g.Eventually(func() int { return counter.Load() }).Should(BeNumerically(">", 5))
```

### Category 2 — function returning a value

```go
g.Eventually(func() (string, error) {
    return fetchStatus(ctx, id)
}).Should(Equal("ready"))
```

### Category 3 — function accepting a Gomega (preferred for compound assertions)

```go
g.Eventually(func(g Gomega) {
    var obj MyResource
    g.Expect(cli.Get(ctx, key, &obj)).To(Succeed())
    g.Expect(obj.Status.Phase).To(Equal("Ready"))
}, "30s", "250ms").Should(Succeed())
```

**Critical**: use the injected `g` inside the callback — not the outer `Expect`. The outer
`Expect` does not retry on failure; the injected `g` does.

### Timeout / interval

```go
// Positional (legacy): Eventually(fn, timeout, interval)
g.Eventually(fn, "30s", "250ms").Should(Succeed())

// Fluent (preferred):
g.Eventually(fn).
    WithTimeout(30 * time.Second).
    WithPolling(250 * time.Millisecond).
    WithContext(ctx).
    Should(Succeed())
```

### Context integration

```go
// Cancellation stops polling immediately
g.Eventually(fn).WithContext(ctx).Should(Succeed())
```

### Requiring consecutive passes

```go
// Must pass 3 times in a row before succeeding
g.Eventually(fn).MustPassRepeatedly(3).Should(Succeed())
```

## Consistently

Verifies a condition holds throughout a duration (default: 100ms, 10ms interval).
Fails if the matcher ever fails during the window.

```go
g.Consistently(func(g Gomega) {
    g.Expect(queue.Len()).To(BeZero())
}, "2s", "100ms").Should(Succeed())
```

## Bailing out early

Return `StopTrying` from a polling function to abort without a timeout error:

```go
g.Eventually(func() (string, error) {
    status, err := fetchStatus(ctx, id)
    if err != nil {
        return "", StopTrying("permanent error: " + err.Error())
    }
    return status, nil
}).Should(Equal("ready"))
```

Use `TryAgainAfter(d)` to request a specific delay before the next poll:

```go
return "", TryAgainAfter(5 * time.Second).Wrap(err)
```

## Changing defaults

```go
SetDefaultEventuallyTimeout(10 * time.Second)
SetDefaultEventuallyPollingInterval(100 * time.Millisecond)
SetDefaultConsistentlyDuration(5 * time.Second)
```

Or via environment variables:
```
GOMEGA_DEFAULT_EVENTUALLY_TIMEOUT=30s
GOMEGA_DEFAULT_EVENTUALLY_POLLING_INTERVAL=250ms
```
