# Assertions and Exceptions in pytest

<!-- category: testing -->

## Plain asserts
pytest uses Python's plain `assert` statement and rewrites it to provide detailed
introspection of the failing expression, so you rarely need special assertion
methods.

## Expecting exceptions
Use the `pytest.raises` context manager to assert that a block raises a specific
exception: `with pytest.raises(ValueError):`. You can inspect the captured exception
through the `excinfo` object the context manager yields.

## Approximate comparisons
`pytest.approx` compares floating-point numbers with a tolerance, avoiding spurious
failures from rounding, for example `assert result == pytest.approx(0.1 + 0.2)`.
