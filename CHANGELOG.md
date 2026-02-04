# Changelog

All notable changes to mac-sweep will be documented in this file.

## [2.0.0] - 2026-02-04

### Added
- **Architectural rewrite**: `src/` layout with strict `core/` (pure logic) and `cli/` (presentation) split
- **New commands**: `status` (quick overview), `doctor` (health checks), `config` (view/modify settings)
- **Enums + frozen dataclasses**: `Status`, `Category`, `Source`, `RemovalMethod` enums; immutable data models throughout
- **JSON API**: Every command supports `--json` with a stable contract (common envelope: version, command, timestamp)
- **198 tests**: Unit tests for all core modules + integration tests for JSON contract
- **7 cache modules**: Homebrew, Xcode DerivedData, Docker/OrbStack, npm, Yarn, pnpm, pip — implemented as Protocol classes
- **Configuration system**: TOML config file, key=value fallback, environment variables, `config` subcommand
- **Workshop documentation**: Step-by-step guide covering all 7 modules (`docs/workshop.md`)

### Changed
- Project structure moved from `lib/` to `src/mac_sweep/` (standard Python packaging)
- Build system changed to hatchling with `pyproject.toml`
- CLI entry point is now `mac-sweep` (installed via pip) instead of `./sweep`
- Cleanup flag changed from `--execute` to `--mode execute` for clarity
- Cache cleanup uses `--clean` flag (dry-run by default, `--clean --execute` to delete)
- LLM prompt is now a named flag (`--prompt "text"`) instead of a positional argument

### Fixed
- Consistent flag naming across all commands
- Proper exit codes: 0 (success), 1 (error), 2 (nothing to do)

## [1.0.0] - 2026-02-03

### Added
- **LLM-powered cleanup agent**: Natural language commands in English and Spanish
  - `./sweep cleanup "borra hugo y Warp"`
  - Multi-provider support: Claude (Anthropic) and GPT (OpenAI)
  - Auto-detection of configured API key
- **Step-by-step guided cleanup**: One item at a time with `[s]kip / [r]emove / [q]uit`
- **Programmatic mode**: `--list --json` for JSON output, `--items` for direct selection
- **Unified entry point**: `./sweep audit` and `./sweep cleanup`
- **Modular architecture**: Python extracted to `lib/` (testable, lintable)
- **58 unit tests** covering safety, sanitization, LLM response parsing, and classification
- **Security hardening**:
  - Eliminated all `shell=True` subprocess calls
  - Added input validation for all package names and cask tokens
  - Added AppleScript path escaping
  - Fixed `pgrep` false positives with precise matching
  - Added `shlex.quote()` for undo script generation
  - Fixed xargs injection in parallel mdls queries
- Open source preparation: LICENSE (MIT), SECURITY.md, CONTRIBUTING.md

### Changed
- Renamed from `mac-audit` to `mac-sweep`
- Cleanup agent redesigned from "pick numbers" to step-by-step guided flow
- Interactive input reads from `/dev/tty` (works with piped input)
- Log prefix changed from `[audit]` to `[sweep]`
- Report footer links to new GitHub repository

### Fixed
- Cleanup script no longer crashes when called via piped input
- Library cleanup failures are now logged instead of silently swallowed
