"""Health checks for mac-sweep.

Core module: returns data, never prints.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

from mac_sweep.core.models import Diagnostic


def run_checks() -> list[Diagnostic]:
    """Run all health checks and return diagnostics."""
    return [
        check_stale_configs(),
        check_broken_symlinks(),
        check_disk_pressure(),
        check_outdated_audit(),
        check_brew_health(),
    ]


def check_stale_configs() -> Diagnostic:
    """Check for old .plist files for uninstalled apps."""
    stale: list[str] = []
    prefs_dir = os.path.expanduser("~/Library/Preferences")

    if not os.path.isdir(prefs_dir):
        return Diagnostic(
            check="stale_configs",
            status="ok",
            message="Preferences directory not found",
        )

    try:
        installed_apps: set[str] = set()
        for entry in os.listdir("/Applications"):
            if entry.endswith(".app"):
                installed_apps.add(entry.rsplit(".app", 1)[0].lower())

        for f in os.listdir(prefs_dir):
            if not f.endswith(".plist"):
                continue
            # Check if it looks like an app plist with bundle ID
            parts = f.rsplit(".", 1)[0].split(".")
            if len(parts) >= 3:
                app_name = parts[-1].lower()
                if (app_name not in installed_apps
                        and not f.startswith("com.apple.")):
                    stale.append(f)
    except OSError:
        pass

    if not stale:
        return Diagnostic(
            check="stale_configs",
            status="ok",
            message="No orphaned configs detected",
        )

    return Diagnostic(
        check="stale_configs",
        status="warning",
        message=f"{len(stale)} potentially orphaned preference files",
        details=tuple(stale[:10]),  # Limit to 10
    )


def check_broken_symlinks() -> Diagnostic:
    """Check for broken symlinks in brew prefix."""
    broken: list[str] = []

    try:
        result = subprocess.run(
            ["brew", "--prefix"],
            capture_output=True, text=True, timeout=5,
        )
        brew_prefix = result.stdout.strip()
    except Exception:
        return Diagnostic(
            check="broken_symlinks",
            status="ok",
            message="Homebrew not available",
        )

    bin_dir = os.path.join(brew_prefix, "bin")
    if not os.path.isdir(bin_dir):
        return Diagnostic(
            check="broken_symlinks",
            status="ok",
            message="Homebrew bin directory not found",
        )

    try:
        for entry in os.listdir(bin_dir):
            full = os.path.join(bin_dir, entry)
            if os.path.islink(full) and not os.path.exists(full):
                broken.append(entry)
    except OSError:
        pass

    if not broken:
        return Diagnostic(
            check="broken_symlinks",
            status="ok",
            message="No broken symlinks found",
        )

    return Diagnostic(
        check="broken_symlinks",
        status="warning",
        message=f"{len(broken)} broken symlinks in {bin_dir}",
        details=tuple(broken[:10]),
    )


def check_disk_pressure() -> Diagnostic:
    """Warn if free disk space is below 10%."""
    try:
        stat = shutil.disk_usage("/")
        free_pct = stat.free / stat.total * 100
        free_gb = stat.free / (1024**3)

        if free_pct < 5:
            return Diagnostic(
                check="disk_pressure",
                status="error",
                message=f"Critical: only {free_gb:.1f} GB free ({free_pct:.0f}%)",
            )
        elif free_pct < 10:
            return Diagnostic(
                check="disk_pressure",
                status="warning",
                message=f"Low disk space: {free_gb:.1f} GB free ({free_pct:.0f}%)",
            )

        return Diagnostic(
            check="disk_pressure",
            status="ok",
            message=f"Disk space OK ({free_gb:.0f} GB free)",
        )
    except Exception:
        return Diagnostic(
            check="disk_pressure",
            status="warning",
            message="Could not check disk space",
        )


def check_outdated_audit() -> Diagnostic:
    """Check if audit report is older than 24 hours."""
    csv_path = os.path.join("reports", "app-audit-report.csv")

    if not os.path.exists(csv_path):
        return Diagnostic(
            check="outdated_audit",
            status="warning",
            message="No audit report found — run ./sweep audit",
        )

    try:
        mtime = os.path.getmtime(csv_path)
        age_hours = (time.time() - mtime) / 3600

        if age_hours > 24:
            return Diagnostic(
                check="outdated_audit",
                status="warning",
                message=f"Audit report stale ({age_hours:.0f}h old) — run ./sweep audit",
            )

        return Diagnostic(
            check="outdated_audit",
            status="ok",
            message=f"Audit report is current ({age_hours:.0f}h old)",
        )
    except OSError:
        return Diagnostic(
            check="outdated_audit",
            status="warning",
            message="Could not check audit report age",
        )


def check_brew_health() -> Diagnostic:
    """Run brew doctor summary."""
    try:
        result = subprocess.run(
            ["brew", "doctor"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            return Diagnostic(
                check="brew_health",
                status="ok",
                message="Homebrew healthy",
            )

        warnings = [
            line.strip()
            for line in result.stderr.splitlines()
            if line.strip() and line.strip().startswith("Warning:")
        ]
        return Diagnostic(
            check="brew_health",
            status="warning",
            message=f"Homebrew has {len(warnings)} warning(s)",
            details=tuple(warnings[:5]),
        )
    except FileNotFoundError:
        return Diagnostic(
            check="brew_health",
            status="ok",
            message="Homebrew not installed",
        )
    except Exception:
        return Diagnostic(
            check="brew_health",
            status="warning",
            message="Could not run brew doctor",
        )
