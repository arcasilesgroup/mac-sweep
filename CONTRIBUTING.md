# Contributing to mac-sweep

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/arcasilesgroup/mac-sweep.git
cd mac-sweep
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python3 -m pytest tests/ -v
```

## Code Style

- **Python**: Follow PEP 8. Use `ruff check` and `ruff format`. Use `mypy --strict` for type checking.
- **Bash**: Keep scripts shellcheck-clean (`brew install shellcheck && shellcheck scripts/*`).

## Architecture

mac-sweep follows a strict core/CLI separation:

- **`src/mac_sweep/core/`** — Pure business logic. No `print()`, no `sys.exit()`, no TTY reads. Returns data only.
- **`src/mac_sweep/cli/`** — Presentation layer. Argument parsing, terminal output, JSON serialization, file writes.

See `docs/adr/` for Architecture Decision Records.

## Security Considerations

Security is critical for this project. When contributing:

- **Never** use `shell=True` in `subprocess.run()` or similar calls
- **Always** validate package names and cask tokens before using them in commands
- **Always** escape paths before embedding them in AppleScript
- **Never** add `sudo` to any command
- **Never** log API keys or sensitive credentials
- Use `src/mac_sweep/core/sanitize.py` for all input validation and escaping

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Ensure all tests pass (`python3 -m pytest tests/ -v`)
5. Submit a pull request

## Adding New Package Manager Support

To add support for a new package manager (e.g., cargo, go modules):

1. Add data collection to `scripts/collect-data.sh` (bash phase)
2. Add processing to `src/mac_sweep/core/audit.py` (classification)
3. Add removal method to `src/mac_sweep/core/cleanup.py`
4. Add validation to `src/mac_sweep/core/sanitize.py`
5. Add tests for the new validation rules
6. Update the README with the new package manager

## Reporting Issues

- Use GitHub Issues for bugs and feature requests
- For security vulnerabilities, see [SECURITY.md](SECURITY.md)
