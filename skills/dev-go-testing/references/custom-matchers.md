# Adding Your Own Matchers

Doc: https://onsi.github.io/gomega/#adding-your-own-matchers

## Option 1: Composition (preferred for simple cases)

Build from existing matchers — no new types needed:

```go
func BeReady() GomegaMatcher {
    return And(
        HaveField("DeletionTimestamp", BeNil()),
        HaveField("Status.Phase", Equal("Running")),
    )
}
```

## Option 2: gcustom

Import: `"github.com/onsi/gomega/gcustom"`

Build from a plain function + failure template:

```go
var BeValidJSON = gcustom.MakeMatcher(func(actual []byte) (bool, error) {
    var v any
    return json.Unmarshal(actual, &v) == nil, nil
}).WithTemplate("Expected:\n{{.FormattedActual}}\n{{.To}} be valid JSON")
```

Template variables: `{{.FormattedActual}}`, `{{.To}}` (`"to"` / `"not to"`), `{{.Negated}}` (bool).

Parameterised matcher:

```go
func HaveStatusCode(expected int) GomegaMatcher {
    return gcustom.MakeMatcher(func(resp *http.Response) (bool, error) {
        return resp.StatusCode == expected, nil
    }).WithTemplate("Expected response to{{.To}} have status {{.Data}}", expected)
}
```

## Option 3: GomegaMatcher interface (full control)

```go
type myMatcher struct{ expected string }

func (m myMatcher) Match(actual any) (bool, error) {
    s, ok := actual.(string)
    if !ok {
        return false, fmt.Errorf("expected string, got %T", actual)
    }
    return strings.Contains(s, m.expected), nil
}

func (m myMatcher) FailureMessage(actual any) string {
    return fmt.Sprintf("Expected %q to contain %q", actual, m.expected)
}

func (m myMatcher) NegatedFailureMessage(actual any) string {
    return fmt.Sprintf("Expected %q not to contain %q", actual, m.expected)
}

func ContainWord(w string) GomegaMatcher { return myMatcher{expected: w} }
```

## Aborting Eventually polling

Implement `MatchMayChangeInTheFuture(actual any) bool` to signal that retrying is pointless:

```go
func (m myMatcher) MatchMayChangeInTheFuture(actual any) bool {
    // return false when further polling won't help
    return !isTerminalState(actual)
}
```

## Testing custom matchers

Assert on `FailureMessage` and `NegatedFailureMessage` directly:

```go
m := ContainWord("hello")
matched, err := m.Match("say hello world")
g.Expect(err).NotTo(HaveOccurred())
g.Expect(matched).To(BeTrue())

matched, err = m.Match("goodbye")
g.Expect(err).NotTo(HaveOccurred())
g.Expect(matched).To(BeFalse())
g.Expect(m.FailureMessage("goodbye")).To(ContainSubstring("hello"))
```
