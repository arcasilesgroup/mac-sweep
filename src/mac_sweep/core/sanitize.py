"""Input validation and escaping for mac-sweep.

All security-critical sanitization lives here:
- Package name validation
- AppleScript path escaping
- Shell command safety
"""

from __future__ import annotations

import os
import re
import shlex


def validate_cask_token(token: str) -> bool:
    """Validate a Homebrew cask token.

    Cask tokens are lowercase alphanumeric with hyphens.
    Examples: 'warp', 'alt-tab', 'visual-studio-code', 'iterm2'
    """
    return bool(re.match(r'^[a-z0-9][a-z0-9-]*$', token))


def validate_package_name(name: str) -> bool:
    """Validate a package name (npm, pip, brew formula, pipx).

    Allows: alphanumeric, hyphens, underscores, dots, @, /
    Examples: 'express', '@angular/cli', 'python3.12', 'my_package'
    """
    return bool(re.match(r'^[a-zA-Z0-9@][a-zA-Z0-9._@/-]*$', name))


def validate_app_path(path: str) -> bool:
    """Validate that an app path is under /Applications/.

    Prevents path traversal attacks in osascript commands.
    """
    normalized = os.path.normpath(path)
    return normalized.startswith("/Applications/")


def applescript_escape(s: str) -> str:
    """Escape a string for safe embedding in AppleScript double-quoted strings.

    Prevents injection in: move POSIX file "{path}" to trash
    """
    return s.replace('\\', '\\\\').replace('"', '\\"')


def safe_removal_cmd(
    method: str, name: str
) -> tuple[list[str] | None, list[str] | None]:
    """Build a safe removal command as a list (subprocess list form).

    Returns (cmd_list, undo_list) where each is a list of strings.
    Returns (None, None) if the name fails validation.
    """
    if method == "brew_cask":
        if not validate_cask_token(name):
            return None, None
        return (
            ["brew", "uninstall", "--cask", name],
            ["brew", "install", "--cask", name],
        )
    elif method == "brew_formula":
        if not validate_package_name(name):
            return None, None
        return (
            ["brew", "uninstall", name],
            ["brew", "install", name],
        )
    elif method == "npm":
        if not validate_package_name(name):
            return None, None
        return (
            ["npm", "uninstall", "-g", name],
            ["npm", "install", "-g", name],
        )
    elif method == "pipx":
        if not validate_package_name(name):
            return None, None
        return (
            ["pipx", "uninstall", name],
            ["pipx", "install", name],
        )
    elif method == "pip":
        if not validate_package_name(name):
            return None, None
        return (
            ["pip3", "uninstall", "-y", name],
            ["pip3", "install", name],
        )
    return None, None


def cmd_to_display(cmd_list: list[str]) -> str:
    """Convert a command list to a safe display string."""
    return " ".join(shlex.quote(part) for part in cmd_list)


def cmd_to_shell(cmd_list: list[str]) -> str:
    """Convert a command list to a shell-safe string for undo scripts."""
    return " ".join(shlex.quote(part) for part in cmd_list)
