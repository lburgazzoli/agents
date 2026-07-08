# Making Assertions

Doc: https://onsi.github.io/gomega/#making-assertions

## Basic syntax

`Expect` and `Ω` are identical — use `Expect` for readability.

```go
g.Expect(actual).To(matcher)
g.Expect(actual).NotTo(matcher)   // same as .ToNot(matcher)
g.Expect(actual).Should(matcher)  // same as .To() — matters only with Ginkgo async node
```

## Handling errors

Gomega filters non-error values automatically — pass multi-return functions directly:

```go
// Good: pass directly
g.Expect(strconv.Atoi("42")).To(Equal(42))

// Avoid: splitting loses the shorthand
val, err := strconv.Atoi("42")
g.Expect(err).NotTo(HaveOccurred())
g.Expect(val).To(Equal(42))
```

For `error`-only returns use `Succeed()`:

```go
g.Expect(os.Remove(path)).To(Succeed())
```

## Annotating assertions

Append a format string (or lazy func) as the last argument for context on failure:

```go
g.Expect(resp.StatusCode).To(Equal(200), "POST /api/items status")
g.Expect(count).To(BeNumerically(">", 0), "want items in DB, got %d", count)

// Lazy: only evaluated on failure
g.Expect(val).To(Equal(expected), func() string {
    return fmt.Sprintf("computed context: %v", expensiveCall())
})
```

## Adjusting output

Control what Gomega prints on failure via the `format` package:

```go
import "github.com/onsi/gomega/format"

format.MaxLength = 4000          // truncation threshold (default 4000)
format.MaxDepth = 10             // struct recursion depth (default 10)
format.UseStringerRepresentation = true  // use .String() if available
```

Implement `format.GomegaStringer` on a type to control its failure representation:

```go
func (t MyType) GomegaString() string { return fmt.Sprintf("MyType(%v)", t.ID) }
```

## Helper function attribution

When writing assertion helpers, mark them so failures point to the call site:

```go
func expectReady(t *testing.T, obj client.Object) {
    t.Helper() // standard Go — works for non-Ginkgo tests
    g := NewWithT(t)
    g.Expect(obj.GetDeletionTimestamp()).To(BeNil())
}
```

For Ginkgo contexts use `GinkgoHelper()` instead of `t.Helper()`.
