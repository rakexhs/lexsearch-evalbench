# Async and Dependency Injection in FastAPI

<!-- category: web-frameworks -->

## async def path operations
You can declare a path operation with `async def` when it performs awaitable I/O,
such as querying a database with an async driver. FastAPI runs synchronous `def`
path operations in an external threadpool so they do not block the event loop.

## Dependency injection
The `Depends` mechanism lets you declare reusable dependencies, such as database
sessions or authentication checks. Dependencies are resolved before the path
operation runs, and their results are injected as parameters. Dependencies can
themselves depend on other dependencies, forming a tree.

## Background tasks
`BackgroundTasks` lets you schedule work to run after returning a response, which is
useful for sending notifications or writing logs without delaying the client.
