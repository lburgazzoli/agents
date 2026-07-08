# Composing Matchers

Doc: https://onsi.github.io/gomega/#composing-matchers

## And / Or / Not

```go
Expect(n).To(And(BeNumerically(">", 0), BeNumerically("<", 10)))
Expect(n).To(SatisfyAll(BeNumerically(">", 0), BeNumerically("<", 10)))  // alias

Expect(s).To(Or(Equal("foo"), Equal("bar")))
Expect(s).To(SatisfyAny(Equal("foo"), Equal("bar")))  // alias

Expect(s).To(Not(BeEmpty()))
Expect(s).ToNot(BeEmpty())  // same thing
```

`And` and `Or` short-circuit: they stop at the first failing/passing matcher.

## WithTransform

Apply a function to `actual` before matching:

```go
// func(T) S form
Expect(resp).To(WithTransform(func(r *http.Response) int {
    return r.StatusCode
}, Equal(200)))

// func(T) (S, error) form — fails the assertion if the transform returns an error
Expect(data).To(WithTransform(func(b []byte) (map[string]any, error) {
    var m map[string]any
    return m, json.Unmarshal(b, &m)
}, HaveKey("name")))
```

## Satisfy

Lightweight predicate without building a full custom matcher:

```go
Expect(n).To(Satisfy(func(v int) bool { return v%2 == 0 }))
```

## Building named matchers via composition

Prefer composition over `GomegaMatcher` interface for simple cases:

```go
func BePositive() GomegaMatcher {
    return BeNumerically(">", 0)
}

func HaveReadyCondition() GomegaMatcher {
    return HaveField("Status.Conditions",
        ContainElement(And(
            HaveField("Type", Equal("Ready")),
            HaveField("Status", Equal(metav1.ConditionTrue)),
        )),
    )
}

// Usage
Expect(score).To(BePositive())
Expect(obj).To(HaveReadyCondition())
```

## Combining with collection matchers

```go
Expect(items).To(ContainElement(And(
    HaveField("Name", Equal("alpha")),
    HaveField("Ready", BeTrue()),
)))

Expect(items).To(HaveEach(
    Or(HaveField("Status", Equal("ok")), HaveField("Status", Equal("pending"))),
))
```
