"""CLI command: cleanup."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time
from datetime import datetime

from mac_sweep.cli import json_output
from mac_sweep.cli.tty import get_tty_input, has_tty
from mac_sweep.core.cleanup import (
    execute_removal,
    load_candidates,
    select_by_names,
    sort_for_browse,
)
from mac_sweep.core.errors import LLMError, SafetyError
from mac_sweep.core.models import CleanupCandidate
from mac_sweep.core.safety import is_protected, is_running
from mac_sweep.core.sanitize import cmd_to_shell


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the cleanup subcommand."""
    p = subparsers.add_parser(
        "cleanup",
        help="Guided agent to review and remove software",
    )
    p.add_argument("--csv", help="Path to audit CSV")
    p.add_argument("--log-dir", default="reports/cleanup-logs",
                    help="Directory for cleanup logs")
    p.add_argument("--mode", choices=["dry-run", "execute"],
                    default="dry-run")
    p.add_argument("--all-unused", action="store_true",
                    help="Include Unknown-status items")
    p.add_argument("--list", dest="list_mode", action="store_true",
                    help="List candidates only")
    p.add_argument("--json", dest="as_json", action="store_true",
                    help="Output as JSON")
    p.add_argument("--items", help="Comma-separated item names")
    p.add_argument("--yes", action="store_true",
                    help="Skip per-item confirmation")
    p.add_argument("--prompt", help="Natural language prompt for LLM")
    p.add_argument("--browse", action="store_true",
                    help="Browse all installed apps for manual uninstall")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the cleanup command."""
    log_lines: list[str] = []

    def log(msg: str) -> None:
        print(msg, file=sys.stderr)
        log_lines.append(msg)

    # Find CSV
    csv_path = args.csv or "reports/app-audit-report.csv"
    if not os.path.exists(csv_path):
        log(f"Error: No audit report found at {csv_path}")
        log("Run './sweep audit' first to generate the report.")
        return 1

    # Validate flags
    if args.browse and args.all_unused:
        log("Error: --browse already includes all statuses. "
            "Do not combine with --all-unused.")
        return 1

    # Check report age
    csv_mtime = os.path.getmtime(csv_path)
    age_hours = (time.time() - csv_mtime) / 3600
    if age_hours > 24:
        log(f"\033[1;33mWarning: Audit report is {age_hours:.0f} hours old. "
            f"Consider re-running './sweep audit' first.\033[0m")

    # Load candidates
    candidates = load_candidates(
        csv_path, args.all_unused, browse_all=args.browse,
    )

    if args.browse:
        candidates = sort_for_browse(candidates)

    # ── List mode ──
    if args.list_mode:
        if args.as_json:
            data = json_output.cleanup_to_json(
                candidates, mode="browse" if args.browse else "list",
            )
            print(json.dumps(data, indent=2))
        else:
            _print_list(candidates, args.browse, log)
        return 0

    # ── LLM prompt mode ──
    if args.prompt:
        try:
            from mac_sweep.core.llm import query_llm
            llm_items = query_llm(args.prompt, candidates)
            if llm_items is None:
                log("\nNote: No LLM API key configured. "
                    "Natural language mode is unavailable.")
                log("      Set ANTHROPIC_API_KEY or OPENAI_API_KEY "
                    "to enable it.")
                log("      Running in interactive mode instead...\n")
            elif llm_items:
                log(f'\nUnderstanding your request: "{args.prompt}"')
                log(f"\u2192 Matched {len(llm_items)} item(s) from "
                    f"{len(candidates)} candidates.\n")
                candidates = [c for c in candidates
                              if c.name in set(llm_items)]
            else:
                log(f'\nNo items matched your request: "{args.prompt}"')
                return 2
        except LLMError as e:
            log(f"LLM error: {e}")
            log("Falling back to interactive mode.")
        except ImportError:
            log("Warning: LLM agent not available. "
                "Falling back to interactive mode.")

    if not candidates:
        log("No cleanup candidates found.")
        if not args.all_unused and not args.browse:
            log("Tip: Use --all-unused to include Unknown-status items,")
            log("     or --browse to see all removable applications.")
        return 2

    # ── Header ──
    mode_label = ("DRY RUN (use --execute to remove)"
                  if args.mode == "dry-run"
                  else "EXECUTE (removals are real!)")
    mode_color = "\033[1;36m" if args.mode == "dry-run" else "\033[1;33m"

    log(f"\n\u2554{'=' * 48}\u2557")
    log(f"\u2551  mac-sweep cleanup agent{' ' * 24}\u2551")
    log(f"\u2551  {mode_color}Mode: {mode_label}\033[0m"
        f"{' ' * max(0, 46 - len(f'Mode: {mode_label}'))}\u2551")
    if args.browse:
        scope = "Scope: ALL removable apps (browse mode)"
        log(f"\u2551  \033[1;35m{scope}\033[0m"
            f"{' ' * max(0, 48 - len(scope) - 2)}\u2551")
    log(f"\u255a{'=' * 48}\u255d")
    log(f"\nFound {len(candidates)} cleanup candidate(s).")

    # ── Items mode ──
    if args.items:
        item_names = {n.strip() for n in args.items.split(",")}
        matched, unmatched = select_by_names(candidates, item_names)
        if unmatched:
            log(f"Warning: Items not found: {', '.join(sorted(unmatched))}")
        removed, skipped = _run_items_mode(
            matched, args.mode, args.yes, log,
        )
    else:
        # ── Interactive agent ──
        removed, skipped = _run_interactive_agent(
            candidates, args.mode, args.browse, log,
        )

    # ── Summary ──
    log(f"\n{'_' * 50}")
    log("\nSummary:")
    if args.mode == "dry-run":
        log(f"  Reviewed: {len(removed) + len(skipped)} items")
        log(f"  Marked for removal: {len(removed)}")
        log(f"  Skipped: {len(skipped)}")
        if removed:
            log("\nThis was a dry run. To actually remove, add --execute:")
            if args.browse:
                log("  ./sweep cleanup --browse --execute")
            else:
                log("  ./sweep cleanup --execute")
    else:
        log(f"  Removed: {len(removed)}")
        log(f"  Skipped: {len(skipped)}")

    # Write logs
    _write_logs(args.log_dir, removed, args.mode, log_lines)

    return 0


def _print_list(
    candidates: list[CleanupCandidate],
    browse_mode: bool,
    log: object,
) -> None:
    """Print candidates in list format."""
    _log = log  # type: ignore[assignment]
    if not candidates:
        _log("No cleanup candidates found.")
        return
    if browse_mode:
        _log(f"\nBrowsing {len(candidates)} removable application(s):\n")
        current_status = None
        for i, c in enumerate(candidates, 1):
            if c.status != current_status:
                current_status = c.status
                _log(f"\n  -- {current_status} --\n")
            desc = f" -- {c.description}" if c.description else ""
            _log(f"  [{i:2d}] {c.name}{desc}")
            _log(f"       Category: {c.category}  |  "
                 f"Command: {c.display_cmd}")
            _log("")
    else:
        _log(f"\nFound {len(candidates)} cleanup candidate(s):\n")
        for i, c in enumerate(candidates, 1):
            desc = f" -- {c.description}" if c.description else ""
            _log(f"  [{i:2d}] {c.name}{desc}")
            _log(f"       Category: {c.category}  |  Status: {c.status}")
            _log(f"       Command:  {c.display_cmd}")
            _log("")


def _run_interactive_agent(
    candidates: list[CleanupCandidate],
    mode: str,
    browse_mode: bool,
    log: object,
) -> tuple[list[CleanupCandidate], list[CleanupCandidate]]:
    """Step-by-step guided agent."""
    _log = log  # type: ignore[assignment]
    if not has_tty():
        _log("Error: Interactive mode requires a terminal (TTY).")
        _log("Use --list or --items for non-interactive mode.")
        return [], []

    removed: list[CleanupCandidate] = []
    skipped: list[CleanupCandidate] = []

    for i, c in enumerate(candidates):
        _log(f"\n{'_' * 50}")
        _log(f"\n[{i+1}/{len(candidates)}] {c.name}")
        _log(f"  Category:    {c.category}")
        if c.description:
            _log(f"  Description: {c.description}")
        _log(f"  Status:      {c.status}")

        if browse_mode and c.status == "Active":
            _log("  \033[1;33m*** WARNING: This app was used within "
                 "the last 7 days! ***\033[0m")
        elif browse_mode and c.status == "Occasional":
            _log("  \033[1;33m** Note: This app was used within "
                 "the last 30 days. **\033[0m")

        if mode == "dry-run":
            _log(f"  Would run:   {c.display_cmd}")
        else:
            _log(f"  Will run:    {c.display_cmd}")
        _log("")

        if browse_mode and c.status == "Active":
            action = get_tty_input(
                "  [s]kip  [r]emove (actively used!)  [q]uit \u2192 "
            ).lower()
        else:
            action = get_tty_input(
                "  [s]kip  [r]emove  [q]uit \u2192 "
            ).lower()

        if action == "q":
            _log("  Quitting.")
            break
        elif action == "r":
            if mode == "dry-run":
                _log(f"  [DRY RUN] Would execute: {c.display_cmd}")
                removed.append(c)
            else:
                success, msg = _do_removal(c, _log)
                if success:
                    removed.append(c)
                else:
                    skipped.append(c)
        else:
            _log(f"  Skipped {c.name}")
            skipped.append(c)

    return removed, skipped


def _run_items_mode(
    candidates: list[CleanupCandidate],
    mode: str,
    auto_yes: bool,
    log: object,
) -> tuple[list[CleanupCandidate], list[CleanupCandidate]]:
    """Remove specific items by name."""
    _log = log  # type: ignore[assignment]
    removed: list[CleanupCandidate] = []
    skipped: list[CleanupCandidate] = []

    for c in candidates:
        if mode == "dry-run":
            _log(f"  [DRY RUN] Would execute: {c.display_cmd}")
            removed.append(c)
            continue

        if not auto_yes:
            if not has_tty():
                _log(f"  Skipped {c.name}: no TTY (use --yes)")
                skipped.append(c)
                continue
            answer = get_tty_input(
                f"  Remove {c.name} ({c.display_cmd})? [y/N] "
            ).lower()
            if answer != "y":
                _log(f"  Skipped {c.name}")
                skipped.append(c)
                continue

        success, msg = _do_removal(c, _log)
        if success:
            removed.append(c)
        else:
            skipped.append(c)

    return removed, skipped


def _do_removal(
    c: CleanupCandidate, log: object
) -> tuple[bool, str]:
    """Execute a single removal with safety checks."""
    _log = log  # type: ignore[assignment]

    if is_protected(c.name, c.category):
        _log(f"  BLOCKED: {c.name} is a protected system application")
        return False, "protected"

    if is_running(c.name, c.category):
        _log(f"  {c.name} appears to be running.")
        if has_tty():
            retry = get_tty_input(
                "  Quit the app and [r]etry, or [s]kip? \u2192 "
            ).lower()
            if retry == "r":
                import time
                time.sleep(2)
                if is_running(c.name, c.category):
                    _log(f"  SKIPPED: {c.name} is still running.")
                    return False, "still running"
            else:
                return False, "skipped by user"
        else:
            _log(f"  SKIPPED: {c.name} appears to be running.")
            return False, "running"

    _log(f"  Running: {c.display_cmd}")
    success, msg = execute_removal(c)
    if success:
        _log(f"  Removed {c.name}")
    else:
        _log(f"  Failed: {msg}")
    return success, msg


def _write_logs(
    log_dir: str,
    removed: list[CleanupCandidate],
    mode: str,
    log_lines: list[str],
) -> None:
    """Write cleanup log and undo script."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(log_dir, f"cleanup-{timestamp}.log")
    undo_path = os.path.join(log_dir, f"cleanup-{timestamp}-undo.sh")

    os.makedirs(log_dir, exist_ok=True)

    with open(log_path, "w") as f:
        f.write("\n".join(log_lines) + "\n")

    if removed and mode == "execute":
        undo_lines = [
            "#!/usr/bin/env bash",
            f"# Undo script for cleanup run {timestamp}",
            "# Run this script to reinstall removed items.",
            "set -euo pipefail",
            "",
        ]
        for c in removed:
            undo_lines.append(f"# Undo: {shlex.quote(c.name)} "
                              f"({c.category})")
            if c.undo_cmd:
                undo_lines.append(cmd_to_shell(list(c.undo_cmd)))
            else:
                undo_lines.append(
                    f"# Restore {shlex.quote(c.name)}.app from Trash")
            undo_lines.append("")

        with open(undo_path, "w") as f:
            f.write("\n".join(undo_lines) + "\n")
        os.chmod(undo_path, 0o755)
        print(f"\nLog:  {log_path}", file=sys.stderr)
        print(f"Undo: {undo_path}", file=sys.stderr)
    else:
        print(f"\nLog: {log_path}", file=sys.stderr)
