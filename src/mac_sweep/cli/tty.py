"""TTY-safe input utilities for mac-sweep."""

from __future__ import annotations

import os
import sys


def get_tty_input(prompt: str) -> str:
    """Read input from /dev/tty, not stdin.

    This works even when the script is called via pipe or heredoc.
    """
    try:
        tty = open('/dev/tty', 'r')
        sys.stderr.write(prompt)
        sys.stderr.flush()
        response = tty.readline().strip()
        tty.close()
        return response
    except OSError:
        return ""


def has_tty() -> bool:
    """Check if a TTY is available for interactive input."""
    try:
        fd = os.open('/dev/tty', os.O_RDONLY)
        os.close(fd)
        return True
    except OSError:
        return False
