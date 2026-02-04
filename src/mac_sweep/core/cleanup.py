"""Cleanup logic for mac-sweep.

Pure business logic — no TTY, no I/O, no side effects.
Returns data structures that the CLI layer presents.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess

from mac_sweep.core.config import OSASCRIPT_TIMEOUT, REMOVAL_TIMEOUT
from mac_sweep.core.errors import RemovalError, SafetyError
from mac_sweep.core.models import CleanupCandidate
from mac_sweep.core.safety import (
    is_brew_dependency,
    is_infrastructure,
    is_protected,
    is_running,
)
from mac_sweep.core.sanitize import (
    applescript_escape,
    validate_app_path,
    validate_cask_token,
    validate_package_name,
)

# Status priority for browse mode display ordering
_STATUS_SORT_ORDER = {
    "Dormant": 0, "Unknown": 1, "Occasional": 2, "Active": 3,
}


def load_candidates(
    csv_path: str,
    include_unknown: bool = False,
    browse_all: bool = False,
) -> list[CleanupCandidate]:
    """Load cleanup candidates from the audit CSV report.

    Applies safety filters:
    - Skips Apple system apps (Layer 1)
    - Skips Infrastructure packages
    - Skips brew dependencies (Layer 2)
    - Only includes Dormant (and optionally Unknown) items,
      unless browse_all=True which includes all removable statuses.
    """
    candidates: list[CleanupCandidate] = []

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row.get("Category", "").strip()
            name = row.get("Name", "").strip()
            detail = row.get("Detail", "").strip()
            status = row.get("Status", "").strip()
            description = row.get("Description", "").strip()

            if not name:
                continue

            # Strip emoji from status
            clean_status = re.sub(r'^[^\w]*', '', status).strip()

            # Filter by status
            if browse_all:
                is_candidate = True
            else:
                is_candidate = clean_status == "Dormant"
                if include_unknown:
                    is_candidate = is_candidate or clean_status == "Unknown"
            if not is_candidate:
                continue

            # Safety Layer 1: skip Apple system apps
            if is_protected(name, category):
                continue

            # Infrastructure never removable
            if is_infrastructure(clean_status):
                continue

            # Safety Layer 2: skip brew dependencies
            if category == "Homebrew Formula" and is_brew_dependency(detail):
                continue

            # Determine removal method and build safe commands
            candidate = _build_candidate(
                category, name, detail, clean_status, description,
            )
            if candidate:
                candidates.append(candidate)

    return candidates


def sort_for_browse(
    candidates: list[CleanupCandidate],
) -> list[CleanupCandidate]:
    """Sort candidates: Dormant first, then Unknown, Occasional, Active.

    Within each status group, sort alphabetically by name.
    """
    return sorted(candidates, key=lambda c: (
        _STATUS_SORT_ORDER.get(c.status, 99),
        c.name.lower(),
    ))


def select_by_names(
    candidates: list[CleanupCandidate],
    names: set[str],
) -> tuple[list[CleanupCandidate], set[str]]:
    """Select candidates by name.

    Returns (matched, unmatched_names).
    """
    matched = [c for c in candidates if c.name in names]
    unmatched = names - {c.name for c in matched}
    return matched, unmatched


def execute_removal(candidate: CleanupCandidate) -> tuple[bool, str]:
    """Execute a single removal.

    Returns (success, message).
    Raises SafetyError subclasses for safety violations.
    """
    c = candidate

    if c.removal_method == "gui_trash":
        return move_app_to_trash(c.name)
    elif c.removal_cmd:
        return run_removal(list(c.removal_cmd))
    else:
        return False, "No removal method available"


def move_app_to_trash(app_name: str) -> tuple[bool, str]:
    """Move a GUI app to Trash via Finder (osascript).

    Security: validates path is under /Applications/ and escapes
    the path for AppleScript.
    """
    app_path = f"/Applications/{app_name}.app"
    if not os.path.exists(app_path):
        try:
            for d in os.listdir("/Applications"):
                candidate = os.path.join("/Applications", d,
                                         f"{app_name}.app")
                if os.path.exists(candidate):
                    app_path = candidate
                    break
        except OSError:
            pass

    if not os.path.exists(app_path):
        return False, f"Could not find {app_name}.app in /Applications"

    if not validate_app_path(app_path):
        return False, f"Path {app_path} is outside /Applications/"

    safe_path = applescript_escape(app_path)
    script = (f'tell application "Finder"\n'
              f'    move POSIX file "{safe_path}" to trash\n'
              f'end tell')

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=OSASCRIPT_TIMEOUT,
        )
        if result.returncode != 0:
            err = result.stderr.strip()
            if "Operation not permitted" in err:
                return False, f"SIP-protected: cannot move {app_name}.app"
            return False, f"Failed to move {app_name}.app to Trash: {err}"
    except subprocess.TimeoutExpired:
        return False, f"Timeout moving {app_name}.app to Trash"

    # Clean related Library data (best effort)
    _cleanup_library_data(app_name)
    return True, f"Moved {app_name}.app to Trash"


def _cleanup_library_data(app_name: str) -> list[str]:
    """Clean up Library directories for a removed app. Returns log messages."""
    messages: list[str] = []
    lib_dirs = [
        os.path.expanduser(f"~/Library/Caches/{app_name}"),
        os.path.expanduser(f"~/Library/Preferences/{app_name}"),
        os.path.expanduser(f"~/Library/Application Support/{app_name}"),
        os.path.expanduser(f"~/Library/Logs/{app_name}"),
        os.path.expanduser(
            f"~/Library/Saved Application State/{app_name}"),
    ]
    for lib_dir in lib_dirs:
        if os.path.exists(lib_dir):
            safe_lib = applescript_escape(lib_dir)
            script = (f'tell application "Finder"\n'
                      f'    move POSIX file "{safe_lib}" to trash\n'
                      f'end tell')
            try:
                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode == 0:
                    messages.append(f"Cleaned: {lib_dir}")
                else:
                    messages.append(
                        f"Could not clean: {lib_dir} "
                        f"({result.stderr.strip()})"
                    )
            except subprocess.TimeoutExpired:
                messages.append(f"Timeout cleaning: {lib_dir}")
            except Exception as e:
                messages.append(f"Error cleaning: {lib_dir} ({e})")
    return messages


def run_removal(cmd_parts: list[str]) -> tuple[bool, str]:
    """Execute a removal command safely using subprocess list form.

    cmd_parts: list of strings, e.g. ["brew", "uninstall", "hugo"]
    """
    try:
        result = subprocess.run(
            cmd_parts,
            capture_output=True, text=True, timeout=REMOVAL_TIMEOUT,
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def _build_candidate(
    category: str,
    name: str,
    detail: str,
    status: str,
    description: str,
) -> CleanupCandidate | None:
    """Build a CleanupCandidate with validated removal commands."""
    if category == "GUI Application":
        if "cask:" in detail:
            cask_token = detail.split("cask:", 1)[1].strip()
            if not validate_cask_token(cask_token):
                return None
            return CleanupCandidate(
                name=name, category=category, description=description,
                status=status, removal_method="brew_cask",
                removal_cmd=("brew", "uninstall", "--cask", cask_token),
                undo_cmd=("brew", "install", "--cask", cask_token),
            )
        else:
            return CleanupCandidate(
                name=name, category=category, description=description,
                status=status, removal_method="gui_trash",
                removal_cmd=(), undo_cmd=(),
                display_cmd="Move to Trash via Finder",
            )

    elif category == "Homebrew Formula":
        if not validate_package_name(name):
            return None
        return CleanupCandidate(
            name=name, category=category, description=description,
            status=status, removal_method="brew_formula",
            removal_cmd=("brew", "uninstall", name),
            undo_cmd=("brew", "install", name),
        )

    elif category == "npm Global":
        if not validate_package_name(name):
            return None
        return CleanupCandidate(
            name=name, category=category, description=description,
            status=status, removal_method="npm",
            removal_cmd=("npm", "uninstall", "-g", name),
            undo_cmd=("npm", "install", "-g", name),
        )

    elif category == "pipx":
        if not validate_package_name(name):
            return None
        return CleanupCandidate(
            name=name, category=category, description=description,
            status=status, removal_method="pipx",
            removal_cmd=("pipx", "uninstall", name),
            undo_cmd=("pipx", "install", name),
        )

    elif category == "pip":
        if not validate_package_name(name):
            return None
        return CleanupCandidate(
            name=name, category=category, description=description,
            status=status, removal_method="pip",
            removal_cmd=("pip3", "uninstall", "-y", name),
            undo_cmd=("pip3", "install", name),
        )

    return None
