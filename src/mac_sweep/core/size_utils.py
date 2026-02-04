"""Size and file-age utilities for mac-sweep."""

from __future__ import annotations

import os
import time


def format_size(size_bytes: int | float) -> str:
    """Format byte count as human-readable string (e.g. '4.2 GB', '128 MB')."""
    if size_bytes < 0:
        return "0 B"
    if size_bytes < 1024:
        return f"{int(size_bytes)} B"
    value = float(size_bytes)
    for unit in ("KB", "MB", "GB", "TB"):
        value /= 1024.0
        if value < 1024 or unit == "TB":
            if value >= 100:
                return f"{value:.0f} {unit}"
            elif value >= 10:
                return f"{value:.1f} {unit}"
            else:
                return f"{value:.2f} {unit}"
    return f"{value:.2f} TB"


def dir_size(path: str) -> int:
    """Calculate total size of a directory in bytes. Returns 0 if path missing."""
    if not os.path.exists(path):
        return 0
    if os.path.isfile(path):
        try:
            return os.path.getsize(path)
        except OSError:
            return 0
    total = 0
    try:
        for dirpath, _dirnames, filenames in os.walk(path):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                try:
                    total += os.lstat(fpath).st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def file_age_days(path: str) -> float:
    """Return age of a file/dir in days based on mtime. Returns -1 if missing."""
    try:
        mtime = os.stat(path).st_mtime
        return (time.time() - mtime) / 86400.0
    except OSError:
        return -1
