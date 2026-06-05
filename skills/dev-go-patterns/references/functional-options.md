# Functional Options Pattern

Use functional options for any Go constructor that accepts optional configuration. Never use builder patterns.

## Core types

Define a generic option interface and a functional adapter in a shared `util` package:

```go
// util/option.go
package util

type Option[T any] interface {
    ApplyTo(target *T)
}

type FunctionalOption[T any] func(*T)

func (f FunctionalOption[T]) ApplyTo(target *T) {
    f(target)
}
```

## Per-component structure

Each component defines an exported `XxxOptions` struct and a type alias for its option type:

```go
// RendererOption is a generic option for RendererOptions.
type RendererOption = util.Option[RendererOptions]

// RendererOptions holds all optional renderer configuration.
type RendererOptions struct {
    Filters      []types.Filter
    Transformers []types.Transformer
    Cache        cache.Interface
    FileSystem   filesys.FileSystem
}
```

## Constructor

Required args first, variadic options last. Apply options via `ApplyTo`:

```go
func NewRenderer(root string, opts ...RendererOption) (*Renderer, error) {
    o := RendererOptions{
        // sensible defaults here
    }
    for _, opt := range opts {
        opt.ApplyTo(&o)
    }
    // use o.Cache, o.Filters, etc.
}
```

## Naming

- Options struct: exported `XxxOptions` (e.g., `RendererOptions`, `CacheOptions`)
- Option type alias: `XxxOption = util.Option[XxxOptions]`
- Option functions: `WithXxx()` — always `With` prefix, returns the option type

## Adding a new option

1. Add field to the `XxxOptions` struct
2. Create `WithXxx()` function returning `XxxOption`
3. Set sensible default in the constructor (before applying options)
4. Add test in `*_option_test.go`

```go
func WithCache(c cache.Interface) RendererOption {
    return util.FunctionalOption[RendererOptions](func(opts *RendererOptions) {
        opts.Cache = c
    })
}
```

For slice fields, append rather than replace:

```go
func WithFilter(f types.Filter) RendererOption {
    return util.FunctionalOption[RendererOptions](func(opts *RendererOptions) {
        opts.Filters = append(opts.Filters, f)
    })
}
```

## Struct as option

The `XxxOptions` struct can implement `Option[XxxOptions]` itself via an `ApplyTo` method, so the whole struct is passable as an option — useful for bundling a preset configuration:

```go
func (opts RendererOptions) ApplyTo(target *RendererOptions) {
    target.Filters = opts.Filters
    target.Transformers = opts.Transformers
    target.LoadRestrictions = opts.LoadRestrictions
    // ...
}

// Bundle a preset configuration as a struct literal, then pass it
// directly to the constructor alongside individual WithXxx options:
preset := RendererOptions{
    LoadRestrictions: kustomizetypes.LoadRestrictionsNone,
    Filters:          []types.Filter{myFilter},
}

r, err := NewRenderer(root, preset, WithFilter(extraFilter))

// Or inline without a variable:
r, err := NewRenderer(root,
    RendererOptions{
        LoadRestrictions: kustomizetypes.LoadRestrictionsNone,
        Filters:          []types.Filter{myFilter},
    },
    WithFilter(extraFilter),
)
```

## Composition

Options are independent and composable — pass multiple in a single call:

```go
r, err := NewRenderer(root,
    WithCache(myCache),
    WithFilter(filter1),
    WithFilter(filter2),
    WithFileSystem(fsys),
)
```

## Rules

1. **Exported options struct** — `XxxOptions` is exported so callers can inspect or pass the whole struct as an option itself
2. **Immutable after construction** — options are applied in the constructor; the resulting object is safe for concurrent use
3. **New options never break callers** — all options are optional by definition; adding one is a backwards-compatible change
4. **No builder pattern** — functional options replace builders; if migrating, collapse `Builder.WithXxx()` calls into `NewXxx(..., WithXxx())` constructor calls
5. **Defaults in the constructor** — initialize the options struct with sensible defaults before the `for _, opt := range opts` loop
6. **Validate after applying** — if options have constraints (e.g., mutually exclusive), validate after all options are applied, not inside individual `WithXxx()` functions
7. **Append for slices** — `WithFilter()`, `WithTransformer()` etc. append to slice fields rather than replacing them
