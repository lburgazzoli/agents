# Equivalence, Presence, Truthiness, and Panics

Doc: https://onsi.github.io/gomega/#provided-matchers

## Asserting Equivalence

```go
Expect(actual).To(Equal(expected))
// Deep equality via reflect.DeepEqual. Fails on type mismatch.

Expect(actual).To(BeEquivalentTo(expected))
// Converts actual to expected's type before comparing. Safe for type aliases.
// e.g. Expect(MyInt(5)).To(BeEquivalentTo(5))

Expect(actual).To(BeIdenticalTo(expected))
// Uses == (pointer identity for pointers, value identity for scalars).

Expect(actual).To(BeComparableTo(expected, cmpopts.IgnoreUnexported(T{})))
// Uses google/go-cmp with options. Import "github.com/google/go-cmp/cmp/cmpopts".
```

## Asserting Presence

```go
Expect(ptr).To(BeNil())
Expect(val).To(BeZero())    // zero value for its type (0, "", nil, false, etc.)
Expect(val).NotTo(BeZero())
```

## Asserting Truthiness

```go
Expect(ok).To(BeTrue())
Expect(ok).To(BeFalse())

// With explanation (shown in failure message):
Expect(ok).To(BeTrueBecause("condition X must hold because %v", reason))
Expect(ok).To(BeFalseBecause("expected %v to be disabled", name))
```

## Asserting on Panics

Wrap the panicking call in a `func()`:

```go
Expect(func() { code.MustNotFail() }).NotTo(Panic())
Expect(func() { code.ExpectedPanic() }).To(Panic())
Expect(func() { code.ExpectedPanic() }).To(PanicWith("expected message"))
// PanicWith accepts a value or a GomegaMatcher
Expect(func() { panic(42) }).To(PanicWith(Equal(42)))
```
