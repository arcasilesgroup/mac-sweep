"""CLI command: doctor — health checks."""

from __future__ import annotations

import argparse
import json
import sys

from mac_sweep.cli import formatters, json_output
from mac_sweep.core.doctor import run_checks


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the doctor subcommand."""
    p = subparsers.add_parser(
        "doctor",
        help="Run health checks on your system",
    )
    p.add_argument("--json", dest="as_json", action="store_true",
                    help="Output as JSON")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the doctor command."""
    diagnostics = run_checks()

    if args.as_json:
        data = json_output.doctor_to_json(diagnostics)
        print(json.dumps(data, indent=2))
    else:
        print(formatters.format_doctor_output(diagnostics))

    # Exit code based on worst status
    has_error = any(d.status == "error" for d in diagnostics)
    has_warning = any(d.status == "warning" for d in diagnostics)

    if has_error:
        return 1
    if has_warning:
        return 0  # Warnings are informational
    return 0
