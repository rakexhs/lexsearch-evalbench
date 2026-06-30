# Python Virtual Environments

<!-- category: python-tooling -->

## Why
A virtual environment is an isolated Python installation with its own `site-packages`
directory, so projects do not share dependencies and cannot break each other. Each
environment can pin different versions of the same package.

## Creating and activating
Create one with `python -m venv .venv`. Activate it on macOS or Linux with
`source .venv/bin/activate`, and on Windows with `.venv\Scripts\activate`.
Deactivate with the `deactivate` command.

## Dependencies
Install packages with `pip install <package>` while the environment is active.
Record exact versions with `pip freeze > requirements.txt`, and reproduce the
environment elsewhere with `pip install -r requirements.txt`.
