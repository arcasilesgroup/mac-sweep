# ADR-004: JSON API Contract

## Status

Accepted

## Context

mac-sweep needs to support a SwiftUI GUI frontend. The GUI will call
`sweep <command> --json` and parse the stdout output. This requires a stable,
documented JSON contract.

## Decision

Every command supports `--json` output. All JSON responses share a common
envelope:

```json
{
  "version": "2.0.0",
  "command": "<command-name>",
  "timestamp": "<ISO 8601>"
}
```

Command-specific fields are added alongside the envelope fields.

The contract is validated by integration tests in
`tests/integration/test_json_contract.py`.

## Exit Codes

| Code | Meaning |
|------|---------|
| `0`  | Success |
| `1`  | Error   |
| `2`  | Nothing to do |

## Consequences

- Every new command must implement a `*_to_json()` function in
  `cli/json_output.py`
- Integration tests verify that the contract is upheld
- Logs go to stderr, JSON goes to stdout — they never mix
- The `version` field enables future schema evolution
- See `docs/json-api.md` for the full contract reference
