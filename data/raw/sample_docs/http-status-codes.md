# Common HTTP Status Codes

<!-- category: web-fundamentals -->

## Success
200 OK is the standard success response. 201 Created signals that a new resource was
created. 204 No Content means the request succeeded but there is no body to return,
common for DELETE.

## Client errors
400 Bad Request indicates malformed syntax. 401 Unauthorized means authentication is
required or failed, while 403 Forbidden means the user is authenticated but not
allowed. 404 Not Found means the resource does not exist. 429 Too Many Requests
signals rate limiting.

## Server errors
500 Internal Server Error is a generic server failure. 502 Bad Gateway and 503
Service Unavailable indicate upstream or capacity problems, often returned by load
balancers when a backend is down.
