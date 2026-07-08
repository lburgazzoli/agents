# Working with Collections

Doc: https://onsi.github.io/gomega/#working-with-collections

Works with slices, arrays, maps, strings, and channels (for length/emptiness).

## Length and emptiness

```go
Expect(slice).To(BeEmpty())
Expect(slice).NotTo(BeEmpty())
Expect(slice).To(HaveLen(3))
Expect(slice).To(HaveCap(10))
```

## Membership — any element

```go
// ContainElement: at least one element matches
Expect(names).To(ContainElement("alice"))
Expect(names).To(ContainElement(ContainSubstring("ali")))

// Capture the matched element
var matched string
Expect(names).To(ContainElement("alice", &matched))
```

## Membership — subset

```go
// ContainElements: all given elements present, any order, extras allowed
Expect(names).To(ContainElements("alice", "bob"))
Expect(names).To(ContainElements(ContainSubstring("ali"), Equal("bob")))
```

## Exact membership

```go
// ConsistOf: exactly these elements, any order, no extras
Expect(names).To(ConsistOf("alice", "bob", "carol"))
Expect(names).To(ConsistOf(ContainSubstring("ali"), "bob", "carol"))

// Pass a slice with the Elements() wrapper when you have a variable
Expect(names).To(ConsistOf(expectedSlice))
```

## All elements

```go
// HaveEach: every element must match
Expect(scores).To(HaveEach(BeNumerically(">=", 0)))
```

## Map matchers

```go
Expect(m).To(HaveKey("foo"))
Expect(m).To(HaveKey(MatchRegexp(`^prefix_`)))
Expect(m).To(HaveKeyWithValue("foo", "bar"))
Expect(m).To(HaveKeyWithValue("foo", ContainSubstring("ba")))
```

## Composition with typed slices

```go
type Item struct{ Name string; Ready bool }

Expect(items).To(ConsistOf(
    HaveField("Name", Equal("alpha")),
    HaveField("Name", Equal("beta")),
))

Expect(items).To(ContainElement(
    And(HaveField("Name", Equal("alpha")), HaveField("Ready", BeTrue())),
))
```
