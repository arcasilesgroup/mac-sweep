"""Safety layers for mac-sweep.

Five safety layers prevent accidental removal of critical software:
1. Protected Apple system apps (hardcoded whitelist)
2. Homebrew dependency checking
3. Running process detection
4. Dry-run default mode
5. Per-item confirmation

Core module: raises exceptions instead of returning booleans for check_* functions.
Also provides is_* query functions for boolean checks.
"""

from __future__ import annotations

import os
import re
import subprocess

from mac_sweep.core.config import PROCESS_CHECK_TIMEOUT
from mac_sweep.core.errors import (
    DependencyError,
    ProtectedAppError,
    ProtectedPathError,
    RunningProcessError,
)

# ═══════════════════════════════════════════════
# Layer 1: Protected Apple system apps
# ═══════════════════════════════════════════════

APPLE_SYSTEM_APPS: frozenset[str] = frozenset({
    "Activity Monitor", "AirDrop", "App Store", "Automator", "Books",
    "Calculator", "Calendar", "Chess", "Contacts", "Dashboard",
    "Dictionary", "DVD Player", "FaceTime", "Find My", "Finder",
    "Font Book", "Freeform", "GarageBand", "Grapher", "Home",
    "Image Capture", "iMovie", "Keynote", "Keychain Access",
    "Launchpad", "Mail", "Maps", "Messages", "Migration Assistant",
    "Mission Control", "Music", "News", "Notes", "Numbers",
    "Pages", "Photo Booth", "Photos", "Podcasts", "Preview",
    "QuickTime Player", "Reminders", "Safari", "Screenshot",
    "Shortcuts", "Siri", "Stickies", "Stocks", "System Information",
    "System Preferences", "System Settings", "Terminal", "TextEdit",
    "Time Machine", "TV", "Utilities", "VoiceOver Utility", "Weather",
    "Disk Utility",
})


def is_protected(name: str, category: str = "") -> bool:
    """Layer 1: Check if an app is a protected Apple system app."""
    if name in APPLE_SYSTEM_APPS:
        return True
    if name.startswith("macOS "):
        return True
    return False


def check_protected(name: str, category: str = "") -> None:
    """Layer 1: Raise ProtectedAppError if app is protected."""
    if is_protected(name, category):
        raise ProtectedAppError(
            f"{name} is a protected Apple system application"
        )


# ═══════════════════════════════════════════════
# Layer 2: Homebrew dependency checking
# ═══════════════════════════════════════════════

def is_brew_dependency(detail: str | None) -> bool:
    """Check if a brew formula is a dependency of other packages."""
    if not detail:
        return False
    detail_lower = detail.lower()
    return "dependency" in detail_lower and "required by:" in detail_lower


def check_dependency(detail: str | None) -> None:
    """Raise DependencyError if formula is a dependency."""
    if is_brew_dependency(detail):
        raise DependencyError(
            f"Formula is a dependency: {detail}"
        )


# ═══════════════════════════════════════════════
# Layer 3: Running process detection
# ═══════════════════════════════════════════════

def is_running(name: str, category: str = "") -> bool:
    """Check if an application or command is currently running.

    For GUI apps: matches the .app bundle path in process list (precise).
    For CLI tools: uses exact process name match (pgrep -x).
    """
    try:
        if category == "GUI Application":
            result = subprocess.run(
                ["pgrep", "-f",
                 "/Applications/.*" + re.escape(name) + r"\.app/"],
                capture_output=True, text=True,
                timeout=PROCESS_CHECK_TIMEOUT,
            )
        else:
            result = subprocess.run(
                ["pgrep", "-x", name],
                capture_output=True, text=True,
                timeout=PROCESS_CHECK_TIMEOUT,
            )
        return result.returncode == 0
    except Exception:
        # Safe default: assume running if we can't determine
        return True


def check_running(name: str, category: str = "") -> None:
    """Raise RunningProcessError if process is running."""
    if is_running(name, category):
        raise RunningProcessError(
            f"{name} appears to be currently running"
        )


# ═══════════════════════════════════════════════
# Infrastructure filter
# ═══════════════════════════════════════════════

def is_infrastructure(status: str) -> bool:
    """Infrastructure packages (pip, gems) are never offered for removal."""
    return status.strip().lower() == "infrastructure"


# ═══════════════════════════════════════════════
# Path safety for cache cleanup
# ═══════════════════════════════════════════════

_HOME = os.path.expanduser("~")

PROTECTED_PATHS: frozenset[str] = frozenset({
    _HOME,
    os.path.join(_HOME, "Desktop"),
    os.path.join(_HOME, "Documents"),
    os.path.join(_HOME, "Downloads"),
    os.path.join(_HOME, "Pictures"),
    os.path.join(_HOME, "Music"),
    os.path.join(_HOME, "Movies"),
    os.path.join(_HOME, "Library"),
    "/",
    "/Applications",
    "/System",
    "/Users",
    "/usr",
    "/var",
    "/etc",
    "/bin",
    "/sbin",
    "/tmp",
    "/opt",
})

ALLOWED_CACHE_PARENTS: frozenset[str] = frozenset({
    os.path.join(_HOME, "Library", "Caches"),
    os.path.join(_HOME, "Library", "Developer", "Xcode", "DerivedData"),
    os.path.join(_HOME, "Library", "Caches", "Yarn"),
    os.path.join(_HOME, "Library", "Caches", "pip"),
    os.path.join(_HOME, "Library", "pnpm", "store"),
    os.path.join(_HOME, ".npm", "_cacache"),
    os.path.join(_HOME, ".npm"),
})


def is_protected_path(path: str) -> bool:
    """Return True if path must never be deleted.

    A path is safe to delete only if:
    1. It is NOT in PROTECTED_PATHS
    2. It falls under at least one ALLOWED_CACHE_PARENT
    """
    resolved = os.path.realpath(os.path.expanduser(path))

    if resolved in PROTECTED_PATHS:
        return True

    for allowed in ALLOWED_CACHE_PARENTS:
        allowed_resolved = os.path.realpath(allowed)
        if (resolved == allowed_resolved
                or resolved.startswith(allowed_resolved + os.sep)):
            return False

    return True


def check_protected_path(path: str) -> None:
    """Raise ProtectedPathError if path is protected."""
    if is_protected_path(path):
        raise ProtectedPathError(
            f"Path is protected and must not be deleted: {path}"
        )
