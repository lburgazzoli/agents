---
name: dev-go-patterns
description: >
  Go design patterns — functional options, tagless switch instead of if/else chains,
  interface-based DI, and other conventions. Triggers when implementing constructors with
  optional configuration, adding options to existing types, refactoring builder patterns,
  writing chained conditionals or multi-step result validation, or applying Go idioms.
  Read the relevant reference on demand based on context.
user-invocable: false
---

# Go Design Patterns

Match the task to a pattern using the keywords below, then read only that reference.

| Pattern | Keywords | Reference |
|---------|----------|-----------|
| Functional options | `WithXxx`, `Option`, `Options struct`, optional config, constructor options, builder replacement, variadic options | [functional-options](references/functional-options.md) |
| Switch over if chains | `if` / `else if` chains, consecutive guard clauses, validating a call result (`err`, nil, empty), multiple early returns | [switch-case](references/switch-case.md) |
