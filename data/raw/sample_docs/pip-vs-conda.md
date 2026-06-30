# pip vs conda for Package Management

<!-- category: python-tooling -->

## pip
pip installs Python packages from the Python Package Index (PyPI). It manages Python
dependencies only and works inside any virtual environment. Wheels make installation
fast because they ship prebuilt binaries.

## conda
conda is a language-agnostic package and environment manager that can install
non-Python dependencies such as compilers and system libraries. It resolves an
entire environment together, which helps with packages that have heavy native
dependencies.

## Choosing
Use pip with venv for lightweight, pure-Python projects. Prefer conda when you need
complex native libraries, for example certain GPU or scientific stacks, where binary
compatibility across packages matters.
