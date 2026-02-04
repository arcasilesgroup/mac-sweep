# mac-sweep

[![CI](https://github.com/arcasilesgroup/mac-sweep/actions/workflows/ci.yml/badge.svg)](https://github.com/arcasilesgroup/mac-sweep/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![macOS](https://img.shields.io/badge/macOS-Ventura%20%7C%20Sonoma%20%7C%20Sequoia-brightgreen)]()
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen)]()

Audit, analyze, and clean up your Mac from the terminal. mac-sweep scans every installed application, Homebrew formula, and developer package on your system, classifies each one by usage, and helps you reclaim disk space safely.

```
$ mac-sweep status

mac-sweep status
===============================
  Apps installed:       67
  Homebrew formulas:   120
  Packages (npm/pip):  165

  Dormant apps:          5  (3.2 GB reclaimable)
  Dev caches:                (7.4 GB reclaimable)

  Last audit:          2h ago
  Recommendation:      mac-sweep cache --clean
===============================

$ mac-sweep cache

  Developer Cache Analysis
  ==================================================
  Module                      Size   Status
  --------------------------------------------------
  Homebrew Cache           2.33 GB   47 items
  Xcode DerivedData        5.12 GB   23 items
  Docker / OrbStack        1.80 GB   4 items
  npm Cache                  843 MB   1 items
  pip Cache                 312 MB   1 items
  --------------------------------------------------
  Total                   10.41 GB

$ mac-sweep cleanup --list

Found 5 cleanup candidate(s):

  [ 1] hugo -- Configurable static site generator
       Category: Homebrew Formula  |  Status: Dormant
       Command:  brew uninstall hugo

  [ 2] Warp -- Rust-based terminal
       Category: GUI Application  |  Status: Dormant
       Command:  brew uninstall --cask warp
  ...
```

## Why mac-sweep?

Developers accumulate software over years — Homebrew formulas from that one tutorial, apps you tried once, npm globals you forgot about. Eventually you have hundreds of installed items and no idea which ones are safe to remove.

- **"What's even installed on my Mac?"** — You have apps from Homebrew, the App Store, manual installs, npm, pip, and more. No single tool shows them all.
- **"Which ones am I actually using?"** — Something installed 2 years ago might be critical infrastructure or completely forgotten. You need usage data, not guesses.
- **"Is it safe to uninstall this?"** — Homebrew formulas have dependencies. System apps are protected. You need safety checks, not `rm -rf`.
- **"How much space am I wasting?"** — Xcode DerivedData, Docker images, npm caches — developer tools silently consume gigabytes.

mac-sweep answers all of this in seconds.

## Features at a Glance

| Feature | Details |
|:--------|:--------|
| **Full system scan** | 7 sources: `/Applications/`, Homebrew Casks, Formulas, npm, pipx, pip, Ruby Gems |
| **Usage classification** | 5 statuses: Active, Occasional, Dormant, Unknown, Infrastructure |
| **5 safety layers** | Protected apps, dependency checks, running process detection, dry-run default, per-item confirmation |
| **Cache cleanup** | 7 modules: Homebrew, Xcode, Docker, npm, Yarn, pnpm, pip |
| **LLM cleanup** | Natural language in English and Spanish (Claude or GPT, optional) |
| **JSON API** | Every command supports `--json` for scripting and GUI frontends |
| **Zero dependencies** | Python stdlib only — no pip packages required at runtime |

## Installation

**Requirements:** macOS (Ventura or later) with Python 3.10+. No external dependencies.

```bash
# Clone and install
git clone https://github.com/arcasilesgroup/mac-sweep.git
cd mac-sweep
pip install -e .

# Verify
mac-sweep --version
# mac-sweep 2.0.0
```

After installation, the `mac-sweep` command is available globally.

> **Alternative (without pip install):** Run directly with `./scripts/sweep <command>`.

To uninstall:

```bash
pip uninstall mac-sweep
```

## Quick Start: 5 Minutes

### 1. See what's on your Mac

```bash
mac-sweep status
```

```
mac-sweep status
===============================
  Apps installed:       67
  Homebrew formulas:   120
  Packages (npm/pip):  165

  Dormant apps:          5  (3.2 GB reclaimable)
  Dev caches:                (7.4 GB reclaimable)

  Last audit:          2h ago
===============================
```

### 2. Run a full audit

```bash
mac-sweep audit
```

```
Scanning applications...
Scanning Homebrew formulas...
Scanning npm global packages...
Scanning pipx packages...
Scanning pip packages...
Scanning Ruby gems...

Audit complete: 69 apps, 16 formulas, 55 packages (140 total)
Reports saved to reports/
  reports/app-audit-report.md
  reports/app-audit-report.csv
```

### 3. Analyze developer caches

```bash
mac-sweep cache
```

```
  Developer Cache Analysis
  ==================================================
  Module                      Size   Status
  --------------------------------------------------
  Homebrew Cache           2.33 GB   47 items
  Xcode DerivedData        5.12 GB   23 items
  Docker / OrbStack        1.80 GB   4 items
  npm Cache                  843 MB   1 items
  pip Cache                 312 MB   1 items
  --------------------------------------------------
  Total                   10.41 GB
```

### 4. Review cleanup candidates

```bash
mac-sweep cleanup
```

```
╔================================================╗
║  mac-sweep cleanup agent                        ║
║  Mode: DRY RUN (use --execute to remove)        ║
╚================================================╝

Found 5 cleanup candidate(s).

[1/5] hugo
  Category:    Homebrew Formula
  Description: Configurable static site generator
  Status:      Dormant
  Would run:   brew uninstall hugo

  [s]kip  [r]emove  [q]uit →
```

Nothing is removed in dry-run mode. When ready, use `--mode execute`.

### 5. Health check

```bash
mac-sweep doctor
```

```
mac-sweep doctor
===============================
  ✓ Disk space OK (45 GB free)
  ✓ Homebrew healthy
  ⚠ Audit report stale (26h old) -- run mac-sweep audit
  ✓ No broken symlinks detected
  ✓ No orphaned configs detected
===============================
```

## Commands Reference

mac-sweep provides 6 commands. Every command supports `--json` for machine-readable output.

| Command | What it does |
|:--------|:-------------|
| `mac-sweep audit` | Scan your Mac and generate Markdown + CSV reports |
| `mac-sweep cleanup` | Interactive agent to review and remove unused software |
| `mac-sweep cache` | Analyze and clean developer caches (Homebrew, npm, Xcode, Docker, etc.) |
| `mac-sweep status` | Quick overview of installed software and reclaimable space |
| `mac-sweep doctor` | Health checks (disk pressure, broken symlinks, stale configs) |
| `mac-sweep config` | View and modify configuration |

---

### `audit` — Scan your Mac

Scans all installed software and generates a detailed report with usage classification.

```bash
mac-sweep audit                      # Scan and generate reports in reports/
mac-sweep audit --json               # JSON output to stdout
mac-sweep audit --report-dir ./out   # Custom report directory
```

**What gets scanned:**

| Category | Source |
|:---------|:-------|
| GUI Applications | `/Applications/` (2 levels deep) |
| Homebrew Casks | `brew info --json=v2` |
| Homebrew Formulas | `brew list`, `brew leaves` |
| npm Global | `npm list -g` |
| pipx | `pipx list` |
| pip | `pip3 list` |
| Ruby Gems | `gem list` |

Each item is classified by usage:

| Status | Emoji | Meaning | Threshold |
|:-------|:------|:--------|:----------|
| Active | 🟢 | Used recently | Last 7 days |
| Occasional | 🟡 | Used sometimes | 7–30 days |
| Dormant | 🔴 | Not used | 30+ days |
| Unknown | ⚪ | No usage data available | — |
| Infrastructure | ⚙️ | System/language runtime | — |

Usage is detected through multiple signals: running processes, `kMDItemLastUsedDate` (Spotlight), LaunchAgents, cache directory mtimes, and binary access times.

<details>
<summary>Full audit CLI reference</summary>

```
mac-sweep audit [OPTIONS]

Options:
  --json              Output as JSON to stdout
  --data-dir PATH     Path to pre-collected data directory (from collect-data.sh)
  --brew-prefix PATH  Homebrew prefix path (default: auto-detect)
  --report-dir DIR    Directory for report output files (default: reports)
```

</details>

---

### `cleanup` — Remove unused software

An interactive agent that walks you through removing dormant software one item at a time.

```bash
mac-sweep cleanup                            # Dry-run: review candidates interactively
mac-sweep cleanup --mode execute             # Remove with per-item confirmation
mac-sweep cleanup --browse                   # Browse ALL apps, not just dormant
mac-sweep cleanup --list                     # List candidates (non-interactive)
mac-sweep cleanup --list --json              # List candidates as JSON (for scripts)
```

```
[1/3] hugo
  Category:    Homebrew Formula
  Description: Configurable static site generator
  Status:      Dormant (last used > 30 days ago)
  Would run:   brew uninstall hugo

  [s]kip  [r]emove  [q]uit →
```

**LLM-powered mode** (optional, requires API key):

```bash
# Natural language in English or Spanish
mac-sweep cleanup --prompt "remove all dormant Homebrew formulas"
mac-sweep cleanup --prompt "borra las apps que no uso"
mac-sweep cleanup --prompt "delete hugo and Warp" --mode execute
```

**Programmatic mode** (for scripts and CI):

```bash
mac-sweep cleanup --mode execute --items "hugo,Warp" --yes
```

<details>
<summary>Full cleanup CLI reference</summary>

```
mac-sweep cleanup [OPTIONS]

Modes:
  --mode dry-run|execute  Run mode (default: dry-run)
  --list                  List candidates only (non-interactive)

Selection:
  --items NAME,..         Select specific items by name (non-interactive)
  --yes                   Skip per-item confirmation
  --prompt "text"         Natural language request (requires API key)

Filters:
  --all-unused            Include Unknown-status items (not just Dormant)
  --browse                Browse ALL apps for manual uninstall

Input:
  --csv PATH              Path to audit CSV (default: reports/app-audit-report.csv)

Output:
  --json                  JSON output
  --log-dir DIR           Directory for cleanup logs (default: reports/cleanup-logs)
```

</details>

---

### `cache` — Clean developer caches

Analyzes and cleans caches from 7 developer tools.

```bash
mac-sweep cache                              # Analyze: show cache sizes
mac-sweep cache --clean                      # Dry-run: preview what would be cleaned
mac-sweep cache --clean --execute            # Actually clean caches
mac-sweep cache --clean --execute --modules homebrew,npm   # Clean specific caches only
mac-sweep cache --json                       # JSON output
```

```
  Developer Cache Analysis
  ==================================================
  Module                      Size   Status
  --------------------------------------------------
  Homebrew Cache           2.33 GB   47 items
  Xcode DerivedData        5.12 GB   23 items
  Docker / OrbStack        1.80 GB   4 items
  npm Cache                  843 MB   1 items
  Yarn Cache                     -   not found
  pnpm Store                     -   not found
  pip Cache                 312 MB   1 items
  --------------------------------------------------
  Total                   10.41 GB
```

**Supported caches:** Homebrew, Xcode DerivedData, Docker/OrbStack, npm, Yarn, pnpm, pip.

<details>
<summary>Full cache CLI reference</summary>

```
mac-sweep cache [OPTIONS]

Options:
  --clean             Run cleanup (dry-run by default, add --execute to confirm)
  --execute           Actually delete cache files (requires --clean)
  --modules LIST      Comma-separated modules to scan (default: all)
                      Available: homebrew, xcode, docker, npm, yarn, pnpm, pip
  --min-age DAYS      Minimum age in days to clean (default: 7)
  --json              Output as JSON
```

</details>

---

### `status` — Quick overview

A fast summary of your system without running a full audit.

```bash
mac-sweep status                     # Terminal output
mac-sweep status --json              # JSON output
```

```
mac-sweep status
===============================
  Apps installed:       67
  Homebrew formulas:   120
  Packages (npm/pip):  165

  Dormant apps:          5  (3.2 GB reclaimable)
  Dev caches:                (7.4 GB reclaimable)

  Last audit:          2h ago
  Recommendation:      mac-sweep cache --clean
===============================
```

---

### `doctor` — Health checks

Runs diagnostic checks on your system.

```bash
mac-sweep doctor                     # Terminal output
mac-sweep doctor --json              # JSON output
```

```
mac-sweep doctor
===============================
  ✓ Disk space OK (45 GB free)
  ✓ Homebrew healthy
  ⚠ Audit report stale (26h old) -- run mac-sweep audit
  ✗ 3 broken symlinks in /opt/homebrew/bin
  ✓ No orphaned configs detected
===============================
```

**Checks performed:** disk pressure, Homebrew health, audit report freshness, broken symlinks, orphaned configs.

---

### `config` — Configuration

```bash
mac-sweep config show                # Show current config values
mac-sweep config path                # Print config file path
mac-sweep config set active_days 14  # Set a config value
```

## Security

mac-sweep is designed to never damage your system.

### Five Safety Layers

| # | Layer | What it does |
|:--|:------|:-------------|
| 1 | **Protected list** | ~60 Apple system apps are never removable (Safari, Finder, Mail, etc.) |
| 2 | **Dependency check** | Homebrew formulas required by others are blocked |
| 3 | **Running process** | Re-checks before each removal; skips if running |
| 4 | **Dry-run default** | Nothing is removed unless you pass `--mode execute` |
| 5 | **Per-item confirmation** | Each removal requires explicit confirmation |

### Additional Guarantees

- **No `sudo`** — never requests or uses root privileges
- **No shell injection** — all subprocess calls use argument lists, never `shell=True`
- **Input validation** — all package names and paths validated with strict regex
- **Recoverable** — GUI apps are moved to Trash, not deleted
- **LLM sandboxed** — LLM can only select from the known candidate list, never executes arbitrary commands
- **API keys protected** — never logged, printed, or included in reports
- **All data local** — no network calls during audit; LLM is optional

See [SECURITY.md](SECURITY.md) for the full security policy and vulnerability reporting.

## Configuration

mac-sweep works out of the box with no configuration. Optional settings:

```bash
# Config file location
~/.config/mac-sweep/config.toml    # Python 3.11+
~/.config/mac-sweep/config         # Key=value fallback

# Or use environment variables
export ANTHROPIC_API_KEY="sk-ant-..."     # For Claude LLM cleanup
export OPENAI_API_KEY="sk-..."            # For GPT LLM cleanup
```

<details>
<summary>All configuration options</summary>

| Setting | Default | Description |
|:--------|:--------|:------------|
| `active_days` | `7` | Days threshold for Active status |
| `occasional_days` | `30` | Days threshold for Occasional status |
| `min_cache_age_days` | `7` | Min age in days before cache files are cleaned |
| `llm_timeout` | `30` | Timeout in seconds for LLM API calls |
| `removal_timeout` | `120` | Timeout in seconds for removal commands |
| `anthropic_api_key` | — | Anthropic API key for Claude |
| `openai_api_key` | — | OpenAI API key for GPT |
| `extra_protected_apps` | — | Comma-separated list of additional apps to protect from removal |

</details>

## JSON API

Every command supports `--json` for structured output. This makes mac-sweep scriptable and enables GUI frontends.

```bash
mac-sweep audit --json  | jq '.summary.dormant'
mac-sweep cache --json  | jq '.total_human'
mac-sweep status --json | jq '.disk.reclaimable_bytes'
```

All JSON responses include a common envelope:

```json
{
  "version": "2.0.0",
  "command": "audit",
  "timestamp": "2026-02-04T12:00:00"
}
```

See [docs/json-api.md](docs/json-api.md) for the full contract reference.

## FAQ

<details>
<summary><strong>Does mac-sweep work on Linux?</strong></summary>

No. mac-sweep is macOS-only. It relies on macOS-specific APIs (Spotlight metadata, Homebrew, Finder AppleScript) that have no Linux equivalent.
</details>

<details>
<summary><strong>Will it delete files without asking?</strong></summary>

No. The default mode is always dry-run. You must explicitly pass `--mode execute` to perform any removal, and each item requires individual confirmation (unless you also pass `--yes`).
</details>

<details>
<summary><strong>What happens when I remove a GUI app?</strong></summary>

GUI apps are moved to Trash via Finder AppleScript, not deleted. You can restore them from Trash. Homebrew formulas and packages are uninstalled through their respective package managers.
</details>

<details>
<summary><strong>Do I need an API key?</strong></summary>

No. The LLM feature (`--prompt`) is optional. All other features work without any API key or network connection.
</details>

<details>
<summary><strong>How does mac-sweep detect "Dormant" apps?</strong></summary>

Usage is detected through multiple signals: running processes, Spotlight's `kMDItemLastUsedDate`, LaunchAgents, cache directory modification times, and binary access times. If none of these show activity in the last 30 days (configurable), the item is classified as Dormant.
</details>

<details>
<summary><strong>Can I protect specific apps from removal?</strong></summary>

Yes. Set `extra_protected_apps` in your config file:

```bash
mac-sweep config set extra_protected_apps "Docker,iTerm"
```

These apps will be blocked from removal in addition to the built-in Apple system app list.
</details>

<details>
<summary><strong>Does mac-sweep send data over the internet?</strong></summary>

No. All audit data stays local on your machine. The only network call happens when you explicitly use the LLM feature (`--prompt`), which sends app names and your prompt to the configured AI provider. This feature is optional and disabled by default.
</details>

## Project Structure

```
mac-sweep/
├── src/mac_sweep/
│   ├── core/              # Pure business logic (no I/O, no side effects)
│   │   ├── models.py      # Enums + frozen dataclasses
│   │   ├── safety.py      # 5 safety layers
│   │   ├── audit.py       # Scan -> AuditResult
│   │   ├── cleanup.py     # Removal logic
│   │   ├── cache.py       # Cache orchestration
│   │   ├── cache_modules/ # Homebrew, Xcode, Docker, npm, Yarn, pnpm, pip
│   │   ├── doctor.py      # Health checks
│   │   └── llm.py         # Claude/GPT integration (stdlib only)
│   └── cli/               # Presentation layer
│       ├── app.py         # Entry point + argparse
│       ├── commands/      # One module per subcommand
│       ├── formatters.py  # Markdown, CSV, terminal tables
│       └── json_output.py # JSON serialization
├── scripts/
│   ├── sweep              # Bash entry point
│   └── collect-data.sh    # Phase 0 data collection for audit
├── tests/                 # 198 tests (unit + integration)
├── docs/
│   ├── adr/               # Architecture Decision Records
│   ├── json-api.md        # JSON API reference
│   └── workshop.md        # Step-by-step workshop (7 modules)
└── pyproject.toml
```

**Design principle:** `core/` never prints, never calls `sys.exit()`, never reads TTY. It returns data. `cli/` presents it. This separation makes the JSON API possible and keeps business logic testable.

## Development

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Linting
ruff check src/ tests/
mypy --strict src/mac_sweep/
shellcheck scripts/*
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Acknowledgments

Built with Python's standard library only. No external runtime dependencies.

## License

MIT — [Arcasiles Group](https://github.com/arcasilesgroup)
