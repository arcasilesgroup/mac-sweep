#!/usr/bin/env bash
# mac-sweep: Collect system data for audit.
# Phase 0: parallel data collection, then hands off to Python.
# Compatible with macOS default bash (3.x).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPORT_DIR="$PROJECT_DIR/reports"
TMPDIR_AUDIT="${TMPDIR_AUDIT:-$(mktemp -d)}"
trap 'rm -rf "$TMPDIR_AUDIT"' EXIT

mkdir -p "$REPORT_DIR"

log() { printf '\033[1;34m[sweep]\033[0m %s\n' "$*" >&2; }

# ──────────────────────────────────────────────
# Phase 0: Collect system-wide data
# ──────────────────────────────────────────────
log "Phase 0: Collecting system-wide data..."

# ps aux snapshot
ps aux > "$TMPDIR_AUDIT/ps_aux.txt" 2>/dev/null || true

# system_profiler
log "  system_profiler SPApplicationsDataType..."
system_profiler SPApplicationsDataType -json > "$TMPDIR_AUDIT/sysprof.json" 2>/dev/null || echo '{}' > "$TMPDIR_AUDIT/sysprof.json"

# Homebrew
BREW_PREFIX=""
if command -v brew &>/dev/null; then
    BREW_PREFIX="$(brew --prefix 2>/dev/null || echo "")"
    log "  brew info --json=v2..."
    brew info --json=v2 --installed > "$TMPDIR_AUDIT/brew_info.json" 2>/dev/null || echo '{}' > "$TMPDIR_AUDIT/brew_info.json"
    log "  brew leaves..."
    brew leaves > "$TMPDIR_AUDIT/brew_leaves.txt" 2>/dev/null || true
    log "  brew list --formula..."
    brew list --formula > "$TMPDIR_AUDIT/brew_formulas.txt" 2>/dev/null || true
    log "  brew deps --installed..."
    brew deps --installed > "$TMPDIR_AUDIT/brew_deps.txt" 2>/dev/null || true
else
    log "  brew not found, skipping Homebrew"
    echo '{}' > "$TMPDIR_AUDIT/brew_info.json"
fi

# Mac App Store apps
log "  mdfind App Store receipts..."
mdfind "kMDItemAppStoreHasReceipt=1" > "$TMPDIR_AUDIT/appstore_apps.txt" 2>/dev/null || true

# Launch agents
log "  Scanning LaunchAgents..."
cat ~/Library/LaunchAgents/*.plist > "$TMPDIR_AUDIT/launch_agents_content.txt" 2>/dev/null || true

# App paths
log "  Finding .app bundles..."
find /Applications -maxdepth 2 -name "*.app" -type d 2>/dev/null | sort > "$TMPDIR_AUDIT/app_paths.txt"

# App sizes (du -sk in parallel)
log "  Collecting app sizes (parallel x8)..."
cat "$TMPDIR_AUDIT/app_paths.txt" | xargs -P 8 -I{} bash -c '
    p="$1"
    sz="$(du -sk "$p" 2>/dev/null | cut -f1 || echo "0")"
    printf "%s\t%s\n" "$p" "$sz"
' _ {} > "$TMPDIR_AUDIT/app_sizes.txt" 2>/dev/null || true

# Parallel mdls (last used + bundle id + kind)
log "  Querying mdls (parallel x8)..."
cat "$TMPDIR_AUDIT/app_paths.txt" | xargs -P 8 -I{} bash -c '
    p="$1"
    lu="$(mdls -name kMDItemLastUsedDate -raw "$p" 2>/dev/null || echo "(null)")"
    bi="$(mdls -name kMDItemCFBundleIdentifier -raw "$p" 2>/dev/null || echo "(null)")"
    kd="$(mdls -name kMDItemKind -raw "$p" 2>/dev/null || echo "(null)")"
    printf "%s\t%s\t%s\t%s\n" "$p" "$lu" "$bi" "$kd"
' _ {} > "$TMPDIR_AUDIT/mdls_results.txt" 2>/dev/null || true

# npm
NPM_JSON="{}"
if command -v npm &>/dev/null; then
    log "  npm list -g..."
    NPM_JSON="$(npm list -g --depth=0 --json 2>/dev/null || echo "{}")"
    NPM_PREFIX="$(npm prefix -g 2>/dev/null || echo "")"
else
    NPM_PREFIX=""
fi
printf '%s' "$NPM_JSON" > "$TMPDIR_AUDIT/npm_global.json"
printf '%s' "$NPM_PREFIX" > "$TMPDIR_AUDIT/npm_prefix.txt"

# pipx
if command -v pipx &>/dev/null; then
    log "  pipx list..."
    pipx list --short > "$TMPDIR_AUDIT/pipx_list.txt" 2>/dev/null || true
else
    touch "$TMPDIR_AUDIT/pipx_list.txt"
fi

# pip
if command -v pip3 &>/dev/null; then
    log "  pip3 list..."
    pip3 list --format=json > "$TMPDIR_AUDIT/pip_list.json" 2>/dev/null || echo '[]' > "$TMPDIR_AUDIT/pip_list.json"
    log "  pip package descriptions..."
    python3 -c '
import json, sys
try:
    from importlib.metadata import distributions
    descs = {}
    for d in distributions():
        name = d.metadata["Name"]
        summary = d.metadata.get("Summary", "") or ""
        if name:
            descs[name.lower()] = summary
    json.dump(descs, sys.stdout)
except Exception:
    sys.stdout.write("{}")
' > "$TMPDIR_AUDIT/pip_descriptions.json" 2>/dev/null || echo '{}' > "$TMPDIR_AUDIT/pip_descriptions.json"
else
    echo '[]' > "$TMPDIR_AUDIT/pip_list.json"
    echo '{}' > "$TMPDIR_AUDIT/pip_descriptions.json"
fi

# gems
if command -v gem &>/dev/null; then
    log "  gem list..."
    gem list > "$TMPDIR_AUDIT/gem_list.txt" 2>/dev/null || true
    gem environment gemdir > "$TMPDIR_AUDIT/gem_sysdir.txt" 2>/dev/null || true
    gem environment user_gemdir > "$TMPDIR_AUDIT/gem_userdir.txt" 2>/dev/null || true
else
    touch "$TMPDIR_AUDIT/gem_list.txt"
fi

log "Phase 0 complete."

# ──────────────────────────────────────────────
# Phases 1-7: Process data and generate reports
# ──────────────────────────────────────────────
log "Processing data and generating reports..."

export PYTHONPATH="$PROJECT_DIR/src"

# Build Python args
PYTHON_ARGS=(audit --data-dir "$TMPDIR_AUDIT" --brew-prefix "$BREW_PREFIX" --report-dir "$REPORT_DIR")

# Pass through any extra flags (--json, etc.)
for arg in "$@"; do
    PYTHON_ARGS+=("$arg")
done

python3 -m mac_sweep "${PYTHON_ARGS[@]}"

log "Done."
