---
name: dev-go-testing
description: >
  Gomega usage in Go tests — assertions, async polling, matchers, and test setup.
  Triggers on: Gomega, Expect, Eventually, Consistently, HaveOccurred, Succeed,
  MatchError, matcher, assertion, NewWithT, g.Expect, gstruct, HaveField,
  gomega-matchers, jq.Match, writing tests, test setup, ghttp, gexec, gbytes, gleak,
  gmeasure, custom matcher, composing matchers, ContainElement, ConsistOf.
  Read the relevant reference on demand based on context.
user-invocable: false
---

# Go Testing with Gomega

Match the task to a topic using the keywords below, then read only that reference.

| Topic | Keywords | Reference |
|-------|----------|-----------|
| Setup / boilerplate | `NewWithT`, dot import, test setup, `go get gomega` | [setup](references/setup.md) |
| Sync assertions | `Expect`, `Should`, `To`, annotation, output format, `GinkgoHelper` | [assertions](references/assertions.md) |
| Async / polling | `Eventually`, `Consistently`, polling, timeout, async, `StopTrying` | [async](references/async.md) |
| Equivalence / presence / truthiness / panics | `Equal`, `BeNil`, `BeZero`, `BeTrue`, `Panic` | [matchers-equivalence](references/matchers-equivalence.md) |
| Error matchers | `Succeed`, `HaveOccurred`, `MatchError`, error assertion | [matchers-errors](references/matchers-errors.md) |
| Collection matchers | `ContainElement`, `ConsistOf`, `HaveKey`, slice, map, array | [matchers-collections](references/matchers-collections.md) |
| String / JSON / YAML matchers | `ContainSubstring`, `MatchRegexp`, `MatchJSON`, `MatchYAML` | [matchers-strings](references/matchers-strings.md) |
| Struct matchers | `HaveField`, `gstruct`, `MatchFields`, `PointTo`, `IgnoreFields` | [matchers-structs](references/matchers-structs.md) |
| Numbers / times / channels / files / values | `BeNumerically`, `BeTemporally`, `Receive`, `BeClosed`, `BeAnExistingFile`, `WithTransform` | [matchers-numbers](references/matchers-numbers.md) |
| HTTP response matchers | `HaveHTTPStatus`, `HaveHTTPBody`, `HaveHTTPHeaderWithValue` | [matchers-http](references/matchers-http.md) |
| Composing matchers | `And`, `Or`, `Not`, `WithTransform`, `Satisfy`, named matcher | [matchers-compose](references/matchers-compose.md) |
| Custom matchers | `GomegaMatcher`, `gcustom`, `MakeMatcher`, custom, implement matcher | [custom-matchers](references/custom-matchers.md) |
| ghttp (HTTP client testing) | `ghttp`, mock server, HTTP client test | [ghttp](references/ghttp.md) |
| gexec (process testing) | `gexec`, `Session`, process, subprocess, stdout, stderr | [gexec](references/gexec.md) |
| gbytes (byte buffer) | `gbytes`, `Buffer`, byte stream | [gbytes](references/gbytes.md) |
| gleak (goroutine leaks) | `gleak`, goroutine leak, `HaveLeaked` | [gleak](references/gleak.md) |
| gmeasure (benchmarking) | `gmeasure`, benchmark, `Experiment`, performance | [gmeasure](references/gmeasure.md) |
| K8s / operator matchers | `jq.Match`, `k8sm`, `gomega-matchers`, K8s operator, k3s-envtest | [k8s-matchers](references/k8s-matchers.md) |

## Self-Updating This Skill

Source of truth for URLs: [references/resources.md](references/resources.md)

To refresh a reference file when the Gomega library updates:

1. Read `references/resources.md` — find the canonical URL for the section to update.
2. Fetch the relevant section from `https://onsi.github.io/gomega/` using WebFetch.
3. Diff the fetched content against the existing reference file.
4. Update only changed parts; preserve project-specific notes and "Project convention" callouts.
5. `k8s-matchers.md` is sourced from `github.com/lburgazzoli/gomega-matchers` — update separately.
6. Update the `last-reviewed` date in `resources.md`.
