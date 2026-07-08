# Working with Structs

Doc: https://onsi.github.io/gomega/#working-with-structs

## HaveField

Traverse struct fields by name and match the value:

```go
type Person struct {
    Name string
    Address struct{ City string }
}

Expect(p).To(HaveField("Name", Equal("alice")))
Expect(p).To(HaveField("Address.City", Equal("London")))  // dot-notation for nested
Expect(p).To(HaveField("String()", ContainSubstring("alice")))  // call method with ()
```

Combine with collection matchers:

```go
Expect(people).To(ContainElement(HaveField("Name", Equal("alice"))))
Expect(people).To(HaveEach(HaveField("Address.City", Equal("London"))))
```

## gstruct

Import: `"github.com/onsi/gomega/gstruct"`

### MatchFields — partial struct matching

```go
Expect(p).To(gstruct.MatchFields(gstruct.IgnoreExtras, gstruct.Fields{
    "Name": Equal("alice"),
    "Age":  BeNumerically(">", 18),
}))
// IgnoreExtras: fields not listed are ignored
// Use gstruct.MatchAllFields (no option) to require all fields to be listed
```

### MatchAllFields — strict matching

```go
Expect(p).To(gstruct.MatchAllFields(gstruct.Fields{
    "Name":    Equal("alice"),
    "Age":     BeNumerically(">", 18),
    "Address": Ignore(),  // explicitly ignore a field
}))
```

### PointTo — dereference a pointer before matching

```go
Expect(ptr).To(gstruct.PointTo(Equal(42)))
Expect(ptr).To(gstruct.PointTo(HaveField("Name", Equal("alice"))))
```

### Ignore — skip a field in MatchAllFields

```go
gstruct.Ignore()
```

### MatchElements — match a slice by key

```go
Expect(items).To(gstruct.MatchElements(
    func(item Item) string { return item.Name },  // key function
    gstruct.IgnoreExtras,
    gstruct.Elements{
        "alpha": HaveField("Ready", BeTrue()),
    },
))
```
