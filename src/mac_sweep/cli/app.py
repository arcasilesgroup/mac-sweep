"""Main CLI entry point for mac-sweep."""

from __future__ import annotations

import argparse
import sys

from mac_sweep import __version__
from mac_sweep.cli.commands import audit, cache, cleanup, config, doctor, status


def main(argv: list[str] | None = None) -> int:
    """Main entry point for mac-sweep CLI."""
    parser = argparse.ArgumentParser(
        prog="sweep",
        description="mac-sweep: macOS application audit and cleanup toolkit",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"mac-sweep {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Register all commands
    audit.register(subparsers)
    cleanup.register(subparsers)
    cache.register(subparsers)
    status.register(subparsers)
    doctor.register(subparsers)
    config.register(subparsers)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)
