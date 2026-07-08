# Working with HTTP Responses

Doc: https://onsi.github.io/gomega/#working-with-http-responses

Matchers accept an `*http.Response` (or anything that produces one).

## Status

```go
Expect(resp).To(HaveHTTPStatus(200))
Expect(resp).To(HaveHTTPStatus(http.StatusOK))
Expect(resp).To(HaveHTTPStatus(http.StatusOK, http.StatusCreated))  // any of these
Expect(resp).To(HaveHTTPStatus("200 OK"))  // string form also accepted
```

## Body

Reads and closes the body — **call once only**.

```go
Expect(resp).To(HaveHTTPBody("hello world"))
Expect(resp).To(HaveHTTPBody(ContainSubstring("error")))
Expect(resp).To(HaveHTTPBody(MatchJSON(`{"status":"ok"}`)))
```

For `[]byte` or `io.Reader` bodies, wrap accordingly.

## Headers

Header name matching is case-insensitive.

```go
Expect(resp).To(HaveHTTPHeaderWithValue("Content-Type", "application/json"))
Expect(resp).To(HaveHTTPHeaderWithValue("X-Request-Id", Not(BeEmpty())))
Expect(resp).To(HaveHTTPHeaderWithValue("Content-Type", ContainSubstring("json")))
```

## Combined example

```go
resp, err := http.Get(server.URL + "/api/items")
g.Expect(err).NotTo(HaveOccurred())
g.Expect(resp).To(HaveHTTPStatus(http.StatusOK))
g.Expect(resp).To(HaveHTTPHeaderWithValue("Content-Type", ContainSubstring("application/json")))
g.Expect(resp).To(HaveHTTPBody(MatchJSON(`[{"id":1}]`)))
```

For full HTTP client mocking see [ghttp](ghttp.md).
