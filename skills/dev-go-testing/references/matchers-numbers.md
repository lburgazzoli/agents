# Numbers, Times, Channels, Files, and Values

Doc: https://onsi.github.io/gomega/#working-with-numbers-and-times

## Numbers

```go
Expect(n).To(BeNumerically("==", 5))
Expect(n).To(BeNumerically("!=", 0))
Expect(n).To(BeNumerically("<",  10))
Expect(n).To(BeNumerically("<=", 10))
Expect(n).To(BeNumerically(">",  0))
Expect(n).To(BeNumerically(">=", 0))
Expect(n).To(BeNumerically("~",  3.14, 0.01))  // approximately equal within delta
```

Works with any numeric type (`int`, `float64`, etc.).

## Times

```go
Expect(t).To(BeTemporally("==", expected))
Expect(t).To(BeTemporally("<",  time.Now()))
Expect(t).To(BeTemporally("~",  expected, time.Second))  // within duration
```

## Channels

All channel matchers are **non-blocking** — wrap in `Eventually` for async use.

```go
Expect(ch).To(BeClosed())
Expect(ch).NotTo(BeClosed())

// Receive: succeeds if a value is available now (non-blocking)
Expect(ch).To(Receive())
Expect(ch).To(Receive(Equal("hello")))       // also checks the received value
Expect(ch).To(Receive(PointTo(HaveLen(3)))) // pointer to received value

// Capture received value
var msg string
Expect(ch).To(Receive(&msg))

// BeSent: succeeds if a send would not block
Expect(ch).To(BeSent("hello"))
```

Async channel read pattern:

```go
g.Eventually(ch).Should(Receive(Equal("hello")))
g.Eventually(ch).Should(BeClosed())
```

## Files

```go
Expect(path).To(BeAnExistingFile())
Expect(path).To(BeARegularFile())
Expect(path).To(BeADirectory())
Expect(path).To(BeASymlink())
Expect(path).NotTo(BeAnExistingFile())
```

## Values (type assertions)

```go
Expect(val).To(BeAssignableToTypeOf(MyType{}))
Expect(val).To(BeAssignableToTypeOf((*MyInterface)(nil)))  // interface check

// HaveValue: dereferences pointers / channels before matching
Expect(&n).To(HaveValue(Equal(42)))
Expect(ch).To(HaveValue(Equal("msg")))  // receives from channel
```
