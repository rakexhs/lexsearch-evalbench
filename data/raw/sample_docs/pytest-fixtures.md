# pytest Fixtures and Test Structure

<!-- category: testing -->

## Fixtures
A pytest fixture is a function decorated with `@pytest.fixture` that provides setup
data or resources to tests. A test requests a fixture by naming it as a function
argument, and pytest injects the returned value.

## Scope
Fixture `scope` controls how often a fixture is created: `function` (the default)
runs it for every test, while `module` or `session` reuse one instance across many
tests, which is useful for expensive setup like a database connection.

## Parametrization
`@pytest.mark.parametrize` runs the same test with multiple input sets, producing a
separate reported test case for each parameter combination. Fixtures can also be
parametrized to multiply across configurations.
