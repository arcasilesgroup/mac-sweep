"""CLI command: status — quick system overview."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from mac_sweep.cli import formatters, json_output
from mac_sweep.core.cache import analyze_all
from mac_sweep.core.models import Status


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the status subcommand."""
    p = subparsers.add_parser(
        "status",
        help="Quick system status overview",
    )
    p.add_argument("--json", dest="as_json", action="store_true",
                    help="Output as JSON")
    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the status command."""
    csv_path = "reports/app-audit-report.csv"

    data: dict = {  # type: ignore[type-arg]
        "has_audit": os.path.exists(csv_path),
        "audit_age_hours": None,
        "counts": {
            "gui_apps": 0,
            "formulas": 0,
            "packages": 0,
            "dormant": 0,
        },
        "disk": {
            "total_app_bytes": 0,
            "dormant_bytes": 0,
            "cache_bytes": 0,
            "reclaimable_bytes": 0,
        },
    }

    # Audit age
    if data["has_audit"]:
        try:
            mtime = os.path.getmtime(csv_path)
            data["audit_age_hours"] = (time.time() - mtime) / 3600
        except OSError:
            pass

        # Parse CSV for counts
        try:
            import csv
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cat = row.get("Category", "").strip()
                    status = row.get("Status", "").strip()
                    size_str = row.get("Size", "").strip()

                    # Clean emoji from status
                    import re
                    clean_status = re.sub(r'^[^\w]*', '', status).strip()

                    if cat == "GUI Application":
                        data["counts"]["gui_apps"] += 1
                        try:
                            size = int(size_str) if size_str else 0
                            data["disk"]["total_app_bytes"] += size
                            if clean_status == "Dormant":
                                data["disk"]["dormant_bytes"] += size
                        except (ValueError, TypeError):
                            pass
                    elif cat == "Homebrew Formula":
                        data["counts"]["formulas"] += 1
                    else:
                        data["counts"]["packages"] += 1

                    if clean_status == "Dormant":
                        data["counts"]["dormant"] += 1
        except Exception:
            pass

    # Cache analysis (quick)
    try:
        analyses = analyze_all()
        cache_total = sum(a.total_bytes for a in analyses)
        data["disk"]["cache_bytes"] = cache_total
        data["disk"]["reclaimable_bytes"] = (
            data["disk"]["dormant_bytes"] + cache_total
        )
    except Exception:
        pass

    if args.as_json:
        output = json_output.status_to_json(data)
        print(json.dumps(output, indent=2))
    else:
        print(formatters.format_status_output(data))

    return 0
