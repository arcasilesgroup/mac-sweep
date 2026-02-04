# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 2.x     | Yes       |
| 1.x     | No        |

## Security Model

mac-sweep is designed with security as a core principle:

### Five Safety Layers

1. **Protected Apple System Apps**: A hardcoded whitelist of ~60 Apple system apps that can never be removed (Safari, Finder, Mail, etc.)
2. **Dependency Checking**: Homebrew formulas that are dependencies of other packages are blocked from removal
3. **Running Process Detection**: Apps that are currently running are skipped (uses precise path-based matching, not fuzzy grep)
4. **Dry-Run by Default**: The `--execute` flag must be explicitly passed to perform any removal
5. **Per-Item Confirmation**: Each removal requires explicit user confirmation (skippable only with `--yes`)

### Input Validation

- All package names and cask tokens are validated with strict regex patterns
- No `shell=True` in any subprocess call (prevents command injection)
- AppleScript paths are escaped to prevent injection
- Undo scripts use `shlex.quote()` for all generated commands
- LLM responses are validated against the known candidate list (can't inject arbitrary items)

### No Elevated Privileges

- mac-sweep **never** uses `sudo`
- GUI apps are moved to Trash via Finder (recoverable), not deleted
- All operations are scoped to the current user

### API Key Security

- API keys are read from environment variables or `~/.config/mac-sweep/config`
- The config file should have permissions `600` (owner-only read/write)
- API keys are never logged, printed, or included in reports

### Data Privacy

- All audit data stays local on your machine
- No data is sent anywhere except when using the LLM feature (which sends only the list of installed app names + your prompt)
- LLM usage is optional and disabled by default

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Email: [Create a private security advisory](https://github.com/arcasilesgroup/mac-sweep/security/advisories/new)
3. Include: description, steps to reproduce, potential impact

We will respond within 48 hours and provide a fix timeline.
