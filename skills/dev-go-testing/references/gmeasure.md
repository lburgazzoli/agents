# gmeasure — Performance Benchmarking

Repo: https://github.com/onsi/gomega/tree/master/gmeasure

`gmeasure` provides structured performance measurement with statistical summaries.
Intended for benchmarks embedded in test suites, not as a replacement for `go test -bench`.

## Install

```go
import "github.com/onsi/gomega/gmeasure"
```

## Basic usage

```go
func TestPerformance(t *testing.T) {
    g := NewWithT(t)

    experiment := gmeasure.NewExperiment("API latency")
    t.Cleanup(func() { t.Log(experiment.String()) })

    experiment.SampleDuration("list items", func(idx int) {
        _, err := client.ListItems(ctx)
        g.Expect(err).NotTo(HaveOccurred())
    }, gmeasure.SamplingConfig{N: 100})

    stats := experiment.GetStats("list items")
    g.Expect(stats.DurationFor(gmeasure.StatMedian)).To(
        BeNumerically("<", 50*time.Millisecond),
    )
}
```

## Sampling

```go
experiment.SampleDuration(name, func(idx int) { ... }, gmeasure.SamplingConfig{
    N:           100,             // number of samples
    Duration:    10 * time.Second, // or run for this long
    NumParallel: 4,               // parallel workers
})

experiment.SampleValue(name, func(idx int) float64 {
    return measureSomething()
}, gmeasure.SamplingConfig{N: 50})
```

## Statistics

```go
stats := experiment.GetStats(name)
stats.DurationFor(gmeasure.StatMin)
stats.DurationFor(gmeasure.StatMax)
stats.DurationFor(gmeasure.StatMean)
stats.DurationFor(gmeasure.StatMedian)
stats.DurationFor(gmeasure.StatStdDev)
```

## Annotations

```go
experiment.RecordNote("running against staging")
experiment.RecordValue("cache hit rate", hitRate)
```

See the [repo README](https://github.com/onsi/gomega/tree/master/gmeasure) for full API.
