"""CLI command: audit."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from mac_sweep.cli import formatters, json_output
from mac_sweep.core.audit import process_audit


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the audit subcommand."""
    p = subparsers.add_parser(
        "audit",
        help="Scan your Mac and generate audit reports",
    )
    p.add_argument(
        "--json", dest="as_json", action="store_true",
        help="Output as JSON to stdout",
    )
    p.add_argument(
        "--data-dir",
        help="Path to pre-collected data directory (from collect-data.sh)",
    )
    p.add_argument(
        "--brew-prefix", default="",
        help="Homebrew prefix path",
    )
    p.add_argument(
        "--report-dir", default="reports",
        help="Directory for report output files",
    )
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the audit command."""
    tmpdir = getattr(args, "data_dir", None)

    if not tmpdir:
        # Run collect-data.sh to gather data
        script_dir = _find_scripts_dir()
        collect_script = os.path.join(script_dir, "collect-data.sh")

        if not os.path.exists(collect_script):
            print("Error: collect-data.sh not found. "
                  "Run from the project directory.", file=sys.stderr)
            return 1

        # Create temp dir and run collection
        import tempfile
        tmpdir = tempfile.mkdtemp(prefix="mac-sweep-audit-")
        try:
            brew_prefix = ""
            try:
                result = subprocess.run(
                    ["brew", "--prefix"],
                    capture_output=True, text=True, timeout=5,
                )
                brew_prefix = result.stdout.strip()
            except Exception:
                pass

            # We need to run the data collection
            env = os.environ.copy()
            env["TMPDIR_AUDIT"] = tmpdir
            result = subprocess.run(
                ["bash", collect_script],
                env=env,
                timeout=300,
            )
            if result.returncode != 0:
                print("Error: Data collection failed.", file=sys.stderr)
                return 1

            args.brew_prefix = brew_prefix
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        tmpdir = args.data_dir

    brew_prefix = getattr(args, "brew_prefix", "")

    # Process audit data
    audit_result = process_audit(tmpdir, brew_prefix)

    if args.as_json:
        data = json_output.audit_to_json(audit_result)
        print(json.dumps(data, indent=2))
        return 0

    # Generate and write reports
    report_dir = args.report_dir
    os.makedirs(report_dir, exist_ok=True)

    md_path = os.path.join(report_dir, "app-audit-report.md")
    csv_path = os.path.join(report_dir, "app-audit-report.csv")

    md_content = formatters.generate_markdown_report(audit_result)
    csv_content = formatters.generate_csv_report(audit_result)

    with open(md_path, "w") as f:
        f.write(md_content)
    with open(csv_path, "w") as f:
        f.write(csv_content)

    # Summary to stderr
    print(f"Apps: {len(audit_result.apps)}, "
          f"Formulas: {len(audit_result.formulas)}, "
          f"npm: {len(audit_result.npm_packages)}, "
          f"pipx: {len(audit_result.pipx_packages)}, "
          f"pip: {len(audit_result.pip_packages)}, "
          f"gems: {len(audit_result.gem_packages)}",
          file=sys.stderr)
    print(f"Reports: {md_path}, {csv_path}", file=sys.stderr)

    return 0


def _find_scripts_dir() -> str:
    """Find the scripts/ directory relative to the project."""
    # Try relative to cwd
    if os.path.isdir("scripts"):
        return "scripts"
    # Try relative to this file
    pkg_dir = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    scripts = os.path.join(pkg_dir, "scripts")
    if os.path.isdir(scripts):
        return scripts
    return "scripts"
