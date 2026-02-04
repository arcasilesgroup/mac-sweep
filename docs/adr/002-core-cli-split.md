# ADR-002: Core / CLI Separation

## Status

Accepted

## Context

In v1, business logic was mixed with terminal output. Functions like
`run_audit()` both computed results and wrote CSV/Markdown files while printing
progress to stderr. This made the code untestable in isolation and impossible
to consume from a GUI.

## Decision

The codebase is split into two layers:

- **`core/`** contains pure business logic. It **never** calls `print()`,
  `sys.exit()`, or reads from TTY. All functions return data (dataclasses,
  lists, enums). Errors are communicated via exceptions.

- **`cli/`** handles all user interaction: argument parsing, terminal output,
  file writing, TTY input, and JSON serialization.

## Rule

> `core/` returns data. `cli/` presents it.

This is enforced in CI with grep checks:
```yaml
- run: "! grep -rP '\\bprint\\(' src/mac_sweep/core/"
- run: "! grep -r 'sys.exit' src/mac_sweep/core/"
```

## Consequences

- A SwiftUI app can call `python3 -m mac_sweep audit --json` and parse stdout
- Unit tests for core logic don't need to capture stdout
- The same `AuditResult` can be formatted as Markdown, CSV, JSON, or a table
- CLI commands are thin wrappers: call core, format output, return exit code
