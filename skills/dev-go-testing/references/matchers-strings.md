# Working with Strings, JSON, and YAML

Doc: https://onsi.github.io/gomega/#working-with-strings-json-and-yaml

## String matchers

```go
Expect(s).To(ContainSubstring("world"))
Expect(s).To(ContainSubstring("Hello %s", name))  // fmt-style args

Expect(s).To(MatchRegexp(`^\d{4}-\d{2}-\d{2}$`))
Expect(s).To(MatchRegexp(`hello %s`, name))       // fmt-style args

Expect(s).To(HavePrefix("http://"))
Expect(s).To(HaveSuffix(".json"))
```

## JSON

Structural equality — whitespace and key order are ignored:

```go
Expect(body).To(MatchJSON(`{"name":"alice","age":30}`))
Expect(body).To(MatchJSON(`{"age":30, "name": "alice"}`))  // same
```

`body` can be `string`, `[]byte`, or `io.Reader`.

## YAML

```go
Expect(data).To(MatchYAML(`
name: alice
age: 30
`))
```

`data` can be `string` or `[]byte`.

## XML

```go
Expect(data).To(MatchXML(`<root><child/></root>`))
```

## Tip

Combine with `WithTransform` to assert on a sub-field after JSON unmarshalling:

```go
type Resp struct{ Status string }
Expect(body).To(WithTransform(func(b []byte) string {
    var r Resp
    json.Unmarshal(b, &r)
    return r.Status
}, Equal("ok")))
```
