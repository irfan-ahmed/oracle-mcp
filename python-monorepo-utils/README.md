# Monorepo Utils

Utilities for managing Python monorepos with MCP servers, including auto-versioning, release creation, changelog checks, and git hooks.

## Installation

To install the CLI, navigate to the `python-monorepo-utils` directory and run:

```
pip install .
```

This will install the `mono-utils` command-line tool.

## Development Setup

For development, install the package in editable mode:

```
pip install -e .
```

This installs the dependencies: click, gitpython, tomlkit, semver.

For running tests, additionally install pytest:

```
pip install pytest
```

## Usage

The CLI provides the following commands:

### bump-versions

Bumps versions in `pyproject.toml` for each MCP server based on CHANGELOG.md entries. Checks environment variables PR, MERGE, RELEASE to modify versions accordingly and update changelogs if releasing.

```
mono-utils bump-versions
```

### create-release

Aggregates changes from all server changelogs to determine the next monorepo version and creates a release branch.

```
mono-utils create-release
```

### check-changelogs

Checks if changes in src directories have corresponding updates in their CHANGELOG.md. Use `--staged` to check staged changes instead of the current commit.

```
mono-utils check-changelogs
mono-utils check-changelogs --staged
```

### install-hooks

Installs git hooks, including a pre-commit hook that checks for changelog updates on staged changes.

```
mono-utils install-hooks
```

## Running Tests

To run the unit tests, ensure you have pytest installed (you can install it via `pip install pytest`). Then, from the project root, run:

```
pytest tests/
```
