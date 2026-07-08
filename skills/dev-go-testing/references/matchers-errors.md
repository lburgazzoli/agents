# Asserting on Errors

Doc: https://onsi.github.io/gomega/#asserting-on-errors

## Core matchers

```go
Expect(err).To(Succeed())        // err == nil
Expect(err).To(HaveOccurred())   // err != nil
```

## MatchError

Accepts four forms:

```go
// 1. String — checks err.Error() contains the string
Expect(err).To(MatchError("connection refused"))

// 2. error — checks errors.Is(err, target)
Expect(err).To(MatchError(io.EOF))

// 3. GomegaMatcher — applied to err.Error()
Expect(err).To(MatchError(ContainSubstring("timeout")))
Expect(err).To(MatchError(MatchRegexp(`dial tcp .* refused`)))

// 4. Predicate func(error) bool
Expect(err).To(MatchError(func(e error) bool {
    return errors.As(e, &myErr{})
}, "be a myErr"))
```

## Multi-return shorthand

Gomega discards all non-error return values automatically — pass directly:

```go
// Good
Expect(os.ReadFile(path)).To(Equal([]byte("hello")))
Expect(strconv.Atoi("42")).To(Equal(42))

// Also fine for error-only returns
Expect(os.Remove(path)).To(Succeed())
```

## Gotcha

Splitting into separate variables before asserting loses the shorthand and produces
noisier failure output:

```go
// Avoid
val, err := strconv.Atoi(s)
Expect(err).NotTo(HaveOccurred()) // failure message shows only "nil" vs "error"
Expect(val).To(Equal(42))
```
