# HTTP Methods and REST Semantics

<!-- category: web-fundamentals -->

## Methods
GET retrieves a resource and must be safe and idempotent, meaning it does not modify
state. POST creates a new resource or triggers processing and is not idempotent. PUT
replaces a resource and is idempotent. PATCH applies a partial update, and DELETE
removes a resource.

## Idempotency
An idempotent method produces the same server state no matter how many times it is
called with the same payload. GET, PUT, and DELETE are idempotent; POST is not,
which is why retrying a POST can create duplicate resources.

## Status codes
2xx indicates success, 3xx redirection, 4xx a client error such as 404 Not Found or
422 validation failure, and 5xx a server error. 201 Created is the conventional
response to a successful POST that creates a resource.
