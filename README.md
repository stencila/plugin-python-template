# Template for a Stencila Python Plugin

> [!IMPORTANT]
> Stencila's plugin system has been deprecated in favor of support for the Model Context Protocol
> and this repository has been achived.
> For more details see this [PR](https://github.com/stencila/stencila/pull/2646).

This repository provides a starting point for writing a Stencila plugin in Python.
It contains a standard python setup, including:

- [Poetry](https://python-poetry.org) for package management.
- The required dependencies from Stencila ([types](https://pypi.org/project/stencila_types/) and [plugin](https://pypi.org/project/stencila_plugin/))
- Implementation of the Kernel API that simply echoes the input.
- A set of tests that can be run using `pytest`.

To use this repository as a starting point for your own plugin:

- Look for [use this template] on GitHub, and follow instructions.
- Change the folder name under `src` to your chosen name.
- Update the `pyproject.toml` file to reflect your package name, description, and author.
- Update the `tests/conftest.py` file to reflect the location of the plugin script.
