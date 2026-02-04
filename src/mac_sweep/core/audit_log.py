"""Append-only operation log with hash chain.

Provides a tamper-evident log of all operations performed by mac-sweep.
Stored at ~/.config/mac-sweep/audit.log
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone

from mac_sweep.core.config import AUDIT_LOG_FILE, CONFIG_DIR


def _hash_entry(entry: str, prev_hash: str) -> str:
    """Compute SHA-256 hash of entry + previous hash."""
    data = f"{prev_hash}:{entry}"
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _get_last_hash() -> str:
    """Read the last hash from the log file."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return "0" * 64

    try:
        with open(AUDIT_LOG_FILE) as f:
            lines = f.readlines()
        if not lines:
            return "0" * 64
        last_line = lines[-1].strip()
        if not last_line:
            return "0" * 64
        try:
            entry = json.loads(last_line)
            return entry.get("hash", "0" * 64)
        except json.JSONDecodeError:
            return "0" * 64
    except OSError:
        return "0" * 64


def log_operation(
    operation: str,
    target: str,
    result: str,
    details: dict[str, str] | None = None,
) -> None:
    """Append an operation to the audit log.

    Args:
        operation: Type of operation (e.g. "remove", "cache_clean")
        target: What was acted on (e.g. "hugo", "homebrew cache")
        result: Outcome (e.g. "success", "failed", "dry-run")
        details: Optional additional details
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)

    prev_hash = _get_last_hash()

    entry_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "target": target,
        "result": result,
    }
    if details:
        entry_data["details"] = details

    entry_str = json.dumps(entry_data, separators=(",", ":"))
    entry_hash = _hash_entry(entry_str, prev_hash)
    entry_data["hash"] = entry_hash

    log_line = json.dumps(entry_data, separators=(",", ":"))

    try:
        with open(AUDIT_LOG_FILE, "a") as f:
            f.write(log_line + "\n")
    except OSError:
        pass


def read_log() -> list[dict[str, str]]:
    """Read all entries from the audit log."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return []

    entries: list[dict[str, str]] = []
    try:
        with open(AUDIT_LOG_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass

    return entries


def verify_chain() -> tuple[bool, int]:
    """Verify the hash chain integrity.

    Returns (valid, break_index) where break_index is -1 if valid.
    """
    entries = read_log()
    if not entries:
        return True, -1

    prev_hash = "0" * 64
    for i, entry in enumerate(entries):
        stored_hash = entry.pop("hash", "")
        entry_str = json.dumps(entry, separators=(",", ":"))
        expected_hash = _hash_entry(entry_str, prev_hash)
        entry["hash"] = stored_hash

        if stored_hash != expected_hash:
            return False, i
        prev_hash = stored_hash

    return True, -1
