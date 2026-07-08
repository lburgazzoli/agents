# gexec — Testing OS Processes

Repo: https://github.com/onsi/gomega/tree/master/gexec

`gexec` runs OS processes and provides Gomega matchers for their exit code, stdout, and stderr.

## Install

```go
import "github.com/onsi/gomega/gexec"
```

## Basic usage

```go
// Build the binary once (in TestMain or a suite-level setup)
pathToBin, err := gexec.Build("./cmd/myapp")
g.Expect(err).NotTo(HaveOccurred())
defer gexec.CleanupBuildArtifacts()

// Run the binary
cmd := exec.Command(pathToBin, "--flag", "value")
session, err := gexec.Start(cmd, GinkgoWriter, GinkgoWriter)
g.Expect(err).NotTo(HaveOccurred())

// Assert it exits cleanly within 5 seconds
g.Eventually(session, "5s").Should(gexec.Exit(0))

// Or assert it fails
g.Eventually(session, "5s").Should(gexec.Exit(1))
```

## Stream matchers

```go
// stdout / stderr are *gbytes.Buffer
g.Eventually(session.Out).Should(gbytes.Say("server started"))
g.Expect(session.Err.Contents()).To(ContainSubstring("warning"))
```

## Signals and interrupts

```go
session.Interrupt()         // sends SIGINT
session.Terminate()         // sends SIGTERM
session.Kill()              // sends SIGKILL
session.Signal(syscall.SIGUSR1)
```

## Exit matchers

```go
gexec.Exit()        // any exit (process has ended)
gexec.Exit(0)       // specific exit code
```

See the [repo README](https://github.com/onsi/gomega/tree/master/gexec) for full API.
