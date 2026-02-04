# ADR-003: Frozen Dataclasses and Enums

## Status

Accepted

## Context

In v1, data was passed around as mutable dictionaries with string keys. This
led to typos, missing fields, and unclear data contracts. Status values like
`"Active"` and `"Dormant"` were plain strings that could be misspelled.

## Decision

- All status and category values use `enum.Enum` subclasses (`Status`,
  `Category`, `Source`, `RemovalMethod`)
- All data containers use `@dataclass(frozen=True)` to be immutable and
  hashable
- Collection fields in frozen dataclasses use `tuple` instead of `list`
  (since lists are mutable and unhashable)

## Consequences

- Type checkers catch invalid status values at development time
- Dataclass instances can be used as dict keys or set members
- Mutation requires creating new instances (which is intentional)
- `CacheAnalysis` and `CleanResult` are exceptions — they use mutable
  dataclasses because they accumulate data during scanning
- `CleanupCandidate.__post_init__` uses `object.__setattr__` to set computed
  fields on frozen instances
