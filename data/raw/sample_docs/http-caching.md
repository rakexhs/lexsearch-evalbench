# HTTP Caching and Conditional Requests

<!-- category: web-fundamentals -->

## Cache-Control
The `Cache-Control` response header tells clients and proxies how to cache a
response. `max-age` sets how many seconds the response stays fresh, and `no-store`
forbids caching entirely.

## Validators
An `ETag` is an opaque identifier for a specific version of a resource. A client can
send it back in an `If-None-Match` header, and the server replies 304 Not Modified
with no body when the resource is unchanged, saving bandwidth.

## Revalidation
Once a cached response becomes stale, the cache revalidates it with the origin using
a conditional request rather than downloading the whole resource again.
