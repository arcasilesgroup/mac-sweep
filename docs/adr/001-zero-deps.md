# ADR-001: Zero Runtime Dependencies

## Status

Accepted

## Context

mac-sweep is a system maintenance tool that runs on macOS developer machines.
Users may have various Python versions and environments. Adding pip dependencies
would require a virtualenv or risk conflicts with system Python.

## Decision

mac-sweep uses **only the Python standard library** at runtime. No pip
dependencies are required to run the tool.

Development dependencies (pytest, mypy, ruff, etc.) are listed under
`[project.optional-dependencies.dev]` in `pyproject.toml`.

## Consequences

- HTTP calls to LLM APIs use `urllib.request` instead of `requests`
- TOML parsing uses `tomllib` (Python 3.11+) with a key=value fallback for 3.10
- No rich terminal library; formatting is done with plain ANSI codes
- Installation is `pip install .` with no dependency resolution needed
- The tool works immediately on any macOS with Python 3.10+
