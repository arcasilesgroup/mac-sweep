# mac-sweep Workshop: Take Control of Your Mac

> **Duration:** 45–60 minutes
> **Level:** Beginner to intermediate
> **Prerequisites:** macOS (Ventura or later), Python 3.10+, Terminal

---

## What You'll Learn

By the end of this workshop you will be able to:

1. Run a full audit of every installed application, formula, and package on your Mac
2. Read and interpret the audit report (Markdown + CSV)
3. Discover and clean developer caches to free disk space
4. Run health checks and diagnose system issues
5. Use the interactive cleanup agent safely (dry-run first, execute later)
6. Optionally use natural language (LLM) to select cleanup targets
7. Automate maintenance with the JSON API and shell scripts

---

## Setup

```bash
# 1. Clone the repository
git clone https://github.com/arcasilesgroup/mac-sweep.git
cd mac-sweep

# 2. Install
pip install -e .

# 3. Verify
mac-sweep --version
# mac-sweep 2.0.0
```

If you see the version number, you're ready to go.

---

## Module 1: Audit — Know What's Installed

**Objective:** Run your first full system audit and understand what's on your Mac.

### Step 1 — Run the audit

```bash
mac-sweep audit
```

The audit scans 7 sources:

| Source | What it finds |
|:-------|:-------------|
| `/Applications/` | GUI apps (2 levels deep) |
| Homebrew Casks | Apps installed via `brew install --cask` |
| Homebrew Formulas | CLI tools via `brew install` |
| npm Global | Packages from `npm install -g` |
| pipx | Python CLI tools |
| pip | Python packages |
| Ruby Gems | Gem packages |

Expected output:

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

### Step 2 — Try JSON output

```bash
mac-sweep audit --json | python3 -m json.tool | head -30
```

This outputs the full audit as structured JSON — useful for scripting (covered in Module 7).

### Key Concepts: Usage Classification

Every item is classified into one of 5 statuses:

| Status | Emoji | Meaning | Threshold |
|:-------|:------|:--------|:----------|
| Active | 🟢 | Used recently | Within last 7 days |
| Occasional | 🟡 | Used sometimes | 7–30 days ago |
| Dormant | 🔴 | Not used | 30+ days |
| Unknown | ⚪ | No usage data | — |
| Infrastructure | ⚙️ | System/language runtime | — |

Usage is detected through multiple signals: running processes, Spotlight's `kMDItemLastUsedDate`, LaunchAgents, cache directory modification times, and binary access times.

### Exercise

> Count how many Dormant items you have. Open `reports/app-audit-report.md` and search for 🔴.

---

## Module 2: Reading the Report

**Objective:** Understand the structure of the audit report and what each section means.

### Anatomy of the Report

Open the Markdown report:

```bash
open reports/app-audit-report.md
```

The report is organized into these sections:

1. **Header** — Timestamp, hostname, mac-sweep version
2. **Status Legend** — Emoji key for the 5 statuses
3. **GUI Applications** — Grouped by installation source
4. **Homebrew Formulas** — Split into "Explicitly Installed" and "Dependencies"
5. **Package Managers** — npm Global, pipx, pip, Ruby Gems
6. **Summary** — Counts by status
7. **Disk Usage** — Size breakdown for GUI apps
8. **Cleanup Guidance** — Next steps

### Sources Explained

GUI apps come from different places:

| Source | Meaning |
|:-------|:--------|
| Homebrew Cask | Installed via `brew install --cask` — easy to uninstall |
| App Store | Downloaded from the Mac App Store |
| Apple | Bundled with macOS (protected, cannot remove) |
| Manual Install | Manually placed in `/Applications/` |
| Unknown | Source could not be determined |

### Dependencies Matter

Some Homebrew formulas are **dependencies** of other formulas. The report marks them:

```
| 🟢 Active | openssl@3 | Required by: curl, wget, python@3.12 |
```

These are blocked from removal by mac-sweep's safety layer — removing them would break other tools.

### CSV Report

For spreadsheet analysis, open the CSV:

```bash
open reports/app-audit-report.csv
```

Columns: `Category`, `Name`, `Source`, `Detail`, `Status`, `Last Used`, `Description`, `Size`

### Exercise

> Find an app with Unknown source and investigate when you last used it.
> Hint: check `Last Used` in the CSV.

---

## Module 3: Cache Cleanup

**Objective:** Discover and clean developer caches to reclaim disk space.

### Step 1 — Analyze caches

```bash
mac-sweep cache
```

This scans 7 developer tool caches without changing anything:

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

Modules that show "not found" simply aren't installed on your machine.

### Step 2 — Dry-run cleanup

```bash
mac-sweep cache --clean
```

This previews what **would** be cleaned (files older than 7 days by default):

```
  Would clean (dry-run):
  --------------------------------------------------
  Homebrew Cache           1.87 GB   (32 items)
  Xcode DerivedData        4.50 GB   (19 items)
  pip Cache                 312 MB   (1 items)
  --------------------------------------------------
  Total freed              6.69 GB   (52 items)

  Run with --execute to actually clean.
```

### Step 3 — Execute cleanup

When you're satisfied with the preview:

```bash
mac-sweep cache --clean --execute
```

This permanently deletes the old cache files. The output confirms what was cleaned.

### Selective Cleanup

Clean only specific caches:

```bash
mac-sweep cache --modules homebrew,npm
mac-sweep cache --clean --execute --modules xcode
```

### Protect Recent Caches

Use `--min-age` to only clean files older than N days:

```bash
mac-sweep cache --clean --execute --min-age 30    # Only caches older than 30 days
```

### JSON Output

```bash
mac-sweep cache --json | python3 -m json.tool
```

### Exercise

> Run the analysis. How much total cache space is recoverable on your Mac?
> Then run `--clean` (dry-run) to see how much would be freed with the 7-day threshold.

---

## Module 4: Health Check

**Objective:** Diagnose the health of your development environment.

### Quick Status

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
  Recommendation:      mac-sweep cache --clean
===============================
```

This gives you a fast overview without running a full audit. It reads the last audit report and scans caches.

### Detailed Health Check

```bash
mac-sweep doctor
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

The doctor runs 5 checks:

| Check | What it tests |
|:------|:-------------|
| `disk_pressure` | Free disk space threshold |
| `brew_health` | `brew doctor` status |
| `outdated_audit` | Whether the audit report is stale (>24h) |
| `broken_symlinks` | Broken symlinks in Homebrew bin |
| `stale_configs` | Orphaned config files for uninstalled apps |

### JSON for Monitoring

Use JSON output to build automated monitoring:

```bash
mac-sweep doctor --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
warnings = [d for d in data['diagnostics'] if d['status'] != 'ok']
if warnings:
    for w in warnings:
        print(f\"[{w['status'].upper()}] {w['message']}\")
    sys.exit(1)
print('All checks passed')
"
```

### Exercise

> Run `mac-sweep doctor`. Do you have any warnings or errors? Try to resolve them.

---

## Module 5: Interactive Cleanup

**Objective:** Use the cleanup agent to review and remove unused software safely.

### Before You Start: The Safety Model

mac-sweep has 5 safety layers that protect you from mistakes:

| # | Layer | Protection |
|:--|:------|:-----------|
| 1 | **Protected list** | ~60 Apple system apps can never be removed |
| 2 | **Dependency check** | Homebrew formulas required by others are blocked |
| 3 | **Running process** | Apps currently running are skipped |
| 4 | **Dry-run default** | Nothing is removed unless you pass `--mode execute` |
| 5 | **Per-item confirm** | Each removal requires explicit confirmation |

### Step 1 — Dry-run (review candidates)

```bash
mac-sweep cleanup
```

This enters interactive mode. Each candidate is presented one at a time:

```
╔================================================╗
║  mac-sweep cleanup agent                        ║
║  Mode: DRY RUN (use --execute to remove)        ║
╚================================================╝

Found 5 cleanup candidate(s).

__________________________________________________

[1/5] hugo
  Category:    Homebrew Formula
  Description: Configurable static site generator
  Status:      Dormant
  Would run:   brew uninstall hugo

  [s]kip  [r]emove  [q]uit →
```

In dry-run mode, choosing `[r]emove` marks the item for removal but does **not** execute anything.

### Step 2 — List candidates (non-interactive)

```bash
mac-sweep cleanup --list
```

This prints all candidates without interaction — useful for reviewing before starting.

### Step 3 — Browse all apps

```bash
mac-sweep cleanup --browse --list
```

By default, cleanup only shows Dormant items. Use `--browse` to see **all** removable apps grouped by status.

### Step 4 — Execute removals

When you're ready:

```bash
mac-sweep cleanup --mode execute
```

Each item still requires confirmation (press `r` to remove, `s` to skip). After execution, mac-sweep generates:

- **Log:** `reports/cleanup-logs/cleanup-YYYYMMDD-HHMMSS.log`
- **Undo script:** `reports/cleanup-logs/cleanup-YYYYMMDD-HHMMSS-undo.sh`

The undo script contains `brew install` commands to reinstall everything you removed.

### Programmatic Removal

For scripts, specify items by name:

```bash
mac-sweep cleanup --mode execute --items "hugo,Warp" --yes
```

### Warning

> Never run `mac-sweep cleanup --mode execute --yes` without reviewing the candidate list first.
> Always do a dry-run or use `--list` to preview candidates.

### Exercise

> Run `mac-sweep cleanup` in dry-run mode. Walk through the candidates.
> Mark 2 items for removal using `[r]`, then quit with `[q]`.
> **Do NOT use `--mode execute`** — this is practice only.

---

## Module 6: LLM Cleanup (Optional)

**Objective:** Configure an LLM provider and use natural language to select cleanup targets.

> This module requires an Anthropic or OpenAI API key. Skip if you don't have one.

### Setup

```bash
# Option 1: Set via config
mac-sweep config set anthropic_api_key sk-ant-api03-...

# Option 2: Use environment variable
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

Verify:

```bash
mac-sweep config show
```

### Natural Language Examples

**English:**

```bash
mac-sweep cleanup --prompt "remove all dormant Homebrew formulas"
mac-sweep cleanup --prompt "delete apps I haven't used in 2 months"
mac-sweep cleanup --prompt "clean up old developer tools"
```

**Spanish:**

```bash
mac-sweep cleanup --prompt "borra las apps que no uso"
mac-sweep cleanup --prompt "elimina las formulas dormant de Homebrew"
```

### How It Works

1. mac-sweep loads the candidate list from the audit CSV
2. Your prompt + the candidate names are sent to the LLM
3. The LLM returns a list of matching item names
4. mac-sweep validates every name against the known candidate list (sandbox)
5. Only validated items are presented for review

**Privacy:** Only app names and your prompt are sent. No file paths, no usage data, no system info.

**Sandboxing:** The LLM cannot add items that aren't already in the candidate list. It cannot execute arbitrary commands.

### Execute with LLM

```bash
# Dry-run first (always)
mac-sweep cleanup --prompt "remove all dormant apps"

# Then execute
mac-sweep cleanup --prompt "remove all dormant apps" --mode execute
```

### Exercise

> Ask the LLM to list apps you haven't used in a month:
> ```bash
> mac-sweep cleanup --prompt "list apps not used in over a month" --list
> ```

---

## Module 7: JSON API & Automation

**Objective:** Use the JSON API to build scripts and automate maintenance tasks.

### The JSON Contract

Every mac-sweep command supports `--json`. All responses share a common envelope:

```json
{
  "version": "2.0.0",
  "command": "audit",
  "timestamp": "2026-02-04T12:00:00"
}
```

### Example 1: Count Dormant Apps

```bash
mac-sweep audit --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
dormant = data['summary']['dormant']
total = data['summary']['total']
print(f'{dormant} dormant out of {total} total items')
"
```

### Example 2: Monitor Cache Growth

```bash
mac-sweep cache --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
for c in data['caches']:
    if c['available']:
        print(f\"{c['label']:.<30} {c['total_human']:>10}\")
print(f\"{'Total':.<30} {data['total_human']:>10}\")
"
```

### Example 3: Health Check Script

```bash
#!/usr/bin/env bash
set -euo pipefail

result=$(mac-sweep doctor --json)
errors=$(echo "$result" | python3 -c "
import json, sys
data = json.load(sys.stdin)
errors = [d for d in data['diagnostics'] if d['status'] == 'error']
print(len(errors))
")

if [ "$errors" -gt 0 ]; then
    echo "ALERT: $errors health check error(s) detected"
    echo "$result" | python3 -m json.tool
    exit 1
fi
echo "All health checks passed"
```

### Example 4: Programmatic Cleanup

```bash
# Get dormant items as JSON, extract names, pass to --items
dormant=$(mac-sweep cleanup --list --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
names = [c['name'] for c in data['candidates']]
print(','.join(names))
")

if [ -n "$dormant" ]; then
    echo "Found dormant items: $dormant"
    mac-sweep cleanup --mode execute --items "$dormant" --yes
fi
```

### Exit Codes

| Code | Meaning |
|:-----|:--------|
| `0` | Success |
| `1` | Error (missing file, invalid args, runtime failure) |
| `2` | Nothing to do (no candidates, no matches) |

### Full JSON API Reference

See [json-api.md](json-api.md) for the complete schema of every command's JSON output.

### Exercise

> Write a one-liner that prints the total reclaimable space:
> ```bash
> mac-sweep status --json | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{d[\"disk\"][\"reclaimable_bytes\"]/1e9:.1f} GB reclaimable')"
> ```

---

## Wrap-Up

### What You Learned

| Module | Command | Skill |
|:-------|:--------|:------|
| 1 | `mac-sweep audit` | Full system scan |
| 2 | — | Reading and interpreting reports |
| 3 | `mac-sweep cache` | Cache analysis and cleanup |
| 4 | `mac-sweep status` / `doctor` | Health monitoring |
| 5 | `mac-sweep cleanup` | Interactive safe removal |
| 6 | `mac-sweep cleanup --prompt` | LLM-powered selection |
| 7 | `--json` | Scripting and automation |

### Recommended Monthly Routine

Run these commands once a month to keep your Mac clean:

```bash
# 1. Quick health check
mac-sweep status

# 2. Full audit (regenerates reports)
mac-sweep audit

# 3. Clean old caches
mac-sweep cache --clean --execute

# 4. Review dormant software
mac-sweep cleanup --list
```

### Next Steps

- Read the [JSON API reference](json-api.md) for full schema details
- Check the [Architecture Decision Records](adr/) for design rationale
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) if you want to contribute

### Feedback

Found an issue? Have a suggestion? [Open an issue](https://github.com/arcasilesgroup/mac-sweep/issues) on GitHub.
