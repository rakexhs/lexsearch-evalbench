# Authentication and Security in FastAPI

<!-- category: web-frameworks -->

## OAuth2 password flow
FastAPI provides `OAuth2PasswordBearer` to extract a bearer token from the
Authorization header. The token is then decoded and verified in a dependency that
returns the current user, raising 401 when the token is missing or invalid.

## Hashing passwords
Never store plaintext passwords. Hash them with a slow algorithm such as bcrypt via
passlib, and verify a login by comparing the hash, not the raw password.

## Scopes
OAuth2 scopes let a token carry fine-grained permissions. A dependency can require a
specific scope and return 403 Forbidden when the authenticated user lacks it.
