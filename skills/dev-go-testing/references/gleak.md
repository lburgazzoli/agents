# gleak — Goroutine Leak Detection

Repo: https://github.com/onsi/gomega/tree/master/gleak

`gleak` detects goroutines that are still running after a test completes.

## Install

```go
import "github.com/onsi/gomega/gleak"
```

## Basic usage

Snapshot goroutines before the test, then assert none leaked at the end:

```go
func TestNoLeaks(t *testing.T) {
    g := NewWithT(t)

    snapshot := gleak.Goroutines()  // capture before

    // ... run code under test ...

    g.Eventually(gleak.Goroutines).ShouldNot(gleak.HaveLeaked(snapshot))
}
```

Use `Eventually` (not `Expect`) because goroutines may take a moment to wind down
after the code under test returns.

## Filtering known goroutines

```go
g.Eventually(gleak.Goroutines).ShouldNot(gleak.HaveLeaked(
    gleak.IgnoringTopFunction("runtime.goexit"),
    gleak.IgnoringInBacktrace("google.golang.org/grpc"),
))
```

Common filters:

```go
gleak.IgnoringTopFunction(name string)   // goroutine's top stack frame contains name
gleak.IgnoringInBacktrace(name string)   // any frame contains name
gleak.IgnoringGoroutines(snapshot)       // ignore all goroutines in snapshot
```

## Suite-level usage

In a test suite setup, capture once before all tests and assert once after all:

```go
func TestMain(m *testing.M) {
    snapshot := gleak.Goroutines()
    code := m.Run()
    // Use a fresh Gomega; can't use Eventually in TestMain easily
    // See docs for Ginkgo DeferCleanup pattern
    _ = snapshot
    os.Exit(code)
}
```

See the [repo README](https://github.com/onsi/gomega/tree/master/gleak) for full API.
