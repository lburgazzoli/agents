# ghttp — Testing HTTP Clients

Doc: https://onsi.github.io/gomega/#ghttp-testing-http-clients
Repo: https://github.com/onsi/gomega/tree/master/ghttp

`ghttp` provides a mock HTTP server that records requests and lets you assert on them.

## Install

```go
import "github.com/onsi/gomega/ghttp"
```

## Basic usage

```go
server := ghttp.NewServer()
t.Cleanup(server.Close)

// Register an expected handler
server.AppendHandlers(
    ghttp.CombineHandlers(
        ghttp.VerifyRequest("GET", "/api/items"),
        ghttp.VerifyHeaderKV("Authorization", "Bearer token"),
        ghttp.RespondWith(http.StatusOK, `[{"id":1}]`, http.Header{
            "Content-Type": []string{"application/json"},
        }),
    ),
)

// Point your client at the mock server
client := NewMyClient(server.URL())
items, err := client.ListItems(ctx)
g.Expect(err).NotTo(HaveOccurred())
g.Expect(items).To(HaveLen(1))

// Assert all expected handlers were called
g.Expect(server.ReceivedRequests()).To(HaveLen(1))
```

## Common handlers

```go
ghttp.VerifyRequest(method, path)
ghttp.VerifyRequest(method, path, rawQuery)       // also match query string
ghttp.VerifyHeaderKV(key, value)
ghttp.VerifyBody(expectedBody)
ghttp.VerifyJSON(expectedJSON)
ghttp.VerifyJSONRepresenting(obj)                 // marshals obj and compares
ghttp.VerifyForm(url.Values{...})

ghttp.RespondWith(statusCode, body)
ghttp.RespondWithJSONEncoded(statusCode, obj)
ghttp.RespondWithProto(statusCode, msg)
```

## TLS

```go
server := ghttp.NewTLSServer()
// server.Client() returns an *http.Client configured to trust the server's cert
```

See the [full docs](https://onsi.github.io/gomega/#ghttp-testing-http-clients) for
request ordering, unlimited handlers, and response delays.
