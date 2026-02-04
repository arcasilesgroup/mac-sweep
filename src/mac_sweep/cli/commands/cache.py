"""CLI command: cache."""

from __future__ import annotations

import argparse
import json
import sys

from mac_sweep.cli import json_output
from mac_sweep.core.cache import analyze_all, clean_all
from mac_sweep.core.cache_modules import list_modules
from mac_sweep.core.config import DEFAULT_MIN_CACHE_AGE_DAYS
from mac_sweep.core.size_utils import format_size


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the cache subcommand."""
    p = subparsers.add_parser(
        "cache",
        help="Analyze and clean development caches",
    )
    p.add_argument("--clean", action="store_true",
                    help="Run cleanup (dry-run by default)")
    p.add_argument("--execute", action="store_true",
                    help="Actually delete cache files")
    p.add_argument("--modules",
                    help="Comma-separated list of modules to scan")
    p.add_argument("--json", dest="as_json", action="store_true",
                    help="Output as JSON")
    p.add_argument("--min-age", type=int, default=DEFAULT_MIN_CACHE_AGE_DAYS,
                    help=f"Minimum age in days to clean "
                         f"(default: {DEFAULT_MIN_CACHE_AGE_DAYS})")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the cache command."""
    modules = None
    if args.modules:
        modules = [m.strip() for m in args.modules.split(",") if m.strip()]

    if args.clean:
        return _run_clean(
            modules=modules, execute=args.execute,
            as_json=args.as_json, min_age_days=args.min_age,
        )
    else:
        return _run_analyze(modules=modules, as_json=args.as_json)


def _run_analyze(
    modules: list[str] | None = None,
    as_json: bool = False,
) -> int:
    """Analyze caches and print report."""
    results = analyze_all(modules)

    if as_json:
        data = json_output.cache_to_json(results)
        print(json.dumps(data, indent=2))
    else:
        _print_table(results)

    return 0


def _run_clean(
    modules: list[str] | None = None,
    execute: bool = False,
    as_json: bool = False,
    min_age_days: int = DEFAULT_MIN_CACHE_AGE_DAYS,
) -> int:
    """Analyze and clean caches."""
    analyses = analyze_all(modules)

    if not as_json:
        _print_table(analyses)
        print(file=sys.stderr)

    clean_results = clean_all(
        analyses, min_age_days=min_age_days, execute=execute,
    )

    if as_json:
        mode = "execute" if execute else "dry-run"
        data = json_output.cache_to_json(
            analyses, clean_results, mode=mode,
        )
        print(json.dumps(data, indent=2))
    else:
        _print_clean_report(clean_results, execute)

    return 0


def _print_table(results: list) -> None:  # type: ignore[type-arg]
    """Print analysis table to stderr."""
    print("\n  Developer Cache Analysis", file=sys.stderr)
    print("  " + "=" * 50, file=sys.stderr)
    print(f"  {'Module':<22} {'Size':>10}   {'Status'}", file=sys.stderr)
    print("  " + "-" * 50, file=sys.stderr)

    total = 0
    for r in results:
        if r.error:
            status = f"error: {r.error}"
        elif not r.available:
            status = "not found"
        else:
            status = f"{len(r.items)} items"
        size_str = format_size(r.total_bytes) if r.available else "-"
        print(f"  {r.label:<22} {size_str:>10}   {status}",
              file=sys.stderr)
        total += r.total_bytes

    print("  " + "-" * 50, file=sys.stderr)
    print(f"  {'Total':<22} {format_size(total):>10}", file=sys.stderr)
    print(file=sys.stderr)


def _print_clean_report(clean_results: list, execute: bool) -> None:  # type: ignore[type-arg]
    """Print cleanup summary to stderr."""
    mode = "Cleaned" if execute else "Would clean (dry-run)"
    print(f"  {mode}:", file=sys.stderr)
    print("  " + "-" * 50, file=sys.stderr)

    total_freed = 0
    total_items = 0
    for cr in clean_results:
        if cr.items_removed > 0:
            print(f"  {cr.label:<22} {format_size(cr.freed_bytes):>10}   "
                  f"({cr.items_removed} items)", file=sys.stderr)
            total_freed += cr.freed_bytes
            total_items += cr.items_removed
        for err in cr.errors:
            print(f"    ! {err}", file=sys.stderr)

    if total_items == 0:
        print("  (nothing to clean)", file=sys.stderr)
    else:
        print("  " + "-" * 50, file=sys.stderr)
        print(f"  {'Total freed':<22} {format_size(total_freed):>10}   "
              f"({total_items} items)", file=sys.stderr)

    if not execute and total_items > 0:
        print("\n  Run with --execute to actually clean.", file=sys.stderr)
    print(file=sys.stderr)
