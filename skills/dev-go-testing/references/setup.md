# Test Setup

Doc: https://onsi.github.io/gomega/#getting-gomega

## Install

```bash
go get github.com/onsi/gomega
```

## Always dot-import

```go
import . "github.com/onsi/gomega"
```

This makes matchers available without the `gomega.` prefix.

## Per-test Gomega instance

Use `NewWithT(t)` — never a package-level `Expect`. This scopes failures to the right `*testing.T`.

```go
func TestFoo(t *testing.T) {
    g := NewWithT(t)

    g.Expect(add(1, 2)).To(Equal(3))
}
```

## Subtests and cleanup

```go
func TestSuite(t *testing.T) {
    g := NewWithT(t)

    // setup
    db := openDB(t)
    g.Expect(db).NotTo(BeNil())

    t.Cleanup(func() { db.Close() })

    t.Run("inserts", func(t *testing.T) {
        testInserts(t, db)
    })

    t.Run("queries", func(t *testing.T) {
        testQueries(t, db)
    })
}
```

## Project convention

- Prefer vanilla Go tests (`testing.T`) over Ginkgo BDD style.
- Use `NewWithT(t)` at the top of every test function.
- Use `t.Cleanup()` for teardown — not `defer` inside helper functions.
