# gbytes — Byte Buffer Matchers

Repo: https://github.com/onsi/gomega/tree/master/gbytes

`gbytes` provides a `Buffer` type and matchers for streaming byte content — typically used
with `gexec` for process stdout/stderr.

## Install

```go
import "github.com/onsi/gomega/gbytes"
```

## Say matcher

Matches content that arrives in the buffer, consuming it up to and including the match:

```go
// Synchronous: content already in buffer
Expect(buffer).To(gbytes.Say("hello"))

// Async: wait for content to arrive
Eventually(buffer).Should(gbytes.Say(`started on port \d+`))  // regexp
```

`Say` accepts a format string like `fmt.Sprintf`:

```go
Eventually(buffer).Should(gbytes.Say("connected to %s", host))
```

## Creating a buffer

```go
buf := gbytes.NewBuffer()
buf.Write([]byte("some output"))

// From a reader (non-blocking)
buf = gbytes.BufferReader(r)
```

## Contents and closedness

```go
Expect(buf.Contents()).To(ContainSubstring("done"))  // full buffer so far
Expect(buf).To(gbytes.Say("final line"))
Expect(buf).To(BeClosed())
```

## With gexec

```go
session, _ := gexec.Start(cmd, GinkgoWriter, GinkgoWriter)
Eventually(session.Out).Should(gbytes.Say("server ready"))
Eventually(session.Err).Should(gbytes.Say(""))  // drain stderr
```

See the [repo README](https://github.com/onsi/gomega/tree/master/gbytes) for full API.
