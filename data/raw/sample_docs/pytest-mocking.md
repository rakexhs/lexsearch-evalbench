# Mocking and Monkeypatching in pytest

<!-- category: testing -->

## monkeypatch
The built-in `monkeypatch` fixture safely sets and restores attributes, environment
variables, and dictionary items for the duration of a test, undoing the change
automatically afterwards.

## unittest.mock
`unittest.mock.patch` replaces an object with a Mock during a test. Patch where the
name is looked up, not where it is defined, otherwise the real object is still used.

## Fakes vs mocks
A fake is a lightweight working implementation, such as an in-memory database, while
a mock records calls so you can assert that a function was invoked with the expected
arguments.
