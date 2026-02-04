"""JSON serialization for mac-sweep.

Consistent JSON output for all commands. Every output includes
version, command, and timestamp.
"""

from __future__ import annotations

from datetime import datetime

from mac_sweep import __version__
from mac_sweep.core.models import (
    AuditResult,
    CacheAnalysis,
    CleanResult,
    CleanupCandidate,
    Diagnostic,
    Status,
)
from mac_sweep.core.size_utils import format_size


def _base(command: str) -> dict:  # type: ignore[type-arg]
    """Create base output dict with version and timestamp."""
    return {
        "version": __version__,
        "command": command,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


def audit_to_json(result: AuditResult) -> dict:  # type: ignore[type-arg]
    """Serialize AuditResult to JSON-compatible dict."""
    data = _base("audit")
    data["hostname"] = result.hostname

    # Summary
    status_counts: dict[str, int] = {
        "active": 0, "occasional": 0, "dormant": 0,
        "unknown": 0, "infrastructure": 0, "total": 0,
    }
    total_size = 0
    dormant_size = 0

    for app in result.apps:
        key = app.status.value.lower()
        if key in status_counts:
            status_counts[key] += 1
        status_counts["total"] += 1
        total_size += app.size_bytes
        if app.status == Status.DORMANT:
            dormant_size += app.size_bytes

    for f in result.formulas:
        key = f.status.value.lower()
        if key in status_counts:
            status_counts[key] += 1
        status_counts["total"] += 1

    for pkg_list in (result.npm_packages, result.pipx_packages):
        for p in pkg_list:
            key = p.status.value.lower()
            if key in status_counts:
                status_counts[key] += 1
            status_counts["total"] += 1

    for p in result.pip_packages:
        status_counts["infrastructure"] += 1
        status_counts["total"] += 1

    for g in result.gem_packages:
        status_counts["infrastructure"] += 1
        status_counts["total"] += 1

    status_counts["total_size_bytes"] = total_size  # type: ignore[assignment]
    status_counts["dormant_size_bytes"] = dormant_size  # type: ignore[assignment]
    data["summary"] = status_counts

    # Apps
    data["apps"] = [
        {
            "name": a.name, "source": a.source, "status": a.status.value,
            "size_bytes": a.size_bytes, "last_used": a.last_used,
            "description": a.description, "detail": a.detail,
        }
        for a in result.apps
    ]

    # Formulas
    data["formulas"] = [
        {
            "name": f.name, "install_type": f.install_type,
            "required_by": f.required_by, "status": f.status.value,
            "description": f.description,
        }
        for f in result.formulas
    ]

    # Packages
    data["npm_packages"] = [
        {
            "name": p.name, "version": p.version,
            "status": p.status.value, "last_used": p.last_used,
            "description": p.description,
        }
        for p in result.npm_packages
    ]

    data["pipx_packages"] = [
        {
            "name": p.name, "version": p.version,
            "status": p.status.value, "last_used": p.last_used,
            "description": p.description,
        }
        for p in result.pipx_packages
    ]

    data["pip_packages"] = [
        {
            "name": p.name, "version": p.version,
            "status": p.status.value, "description": p.description,
        }
        for p in result.pip_packages
    ]

    data["gem_packages"] = [
        {
            "name": g.name, "version": g.version,
            "type": g.extra, "description": g.description,
        }
        for g in result.gem_packages
    ]

    return data


def cleanup_to_json(
    candidates: list[CleanupCandidate],
    mode: str = "list",
) -> dict:  # type: ignore[type-arg]
    """Serialize cleanup candidates to JSON-compatible dict."""
    data = _base("cleanup")
    data["mode"] = mode
    data["candidates"] = [
        {
            "name": c.name,
            "category": c.category,
            "status": c.status,
            "removal_cmd": c.display_cmd,
            "description": c.description,
        }
        for c in candidates
    ]
    data["total"] = len(candidates)
    return data


def cache_to_json(
    analyses: list[CacheAnalysis],
    clean_results: list[CleanResult] | None = None,
    mode: str = "analyze",
) -> dict:  # type: ignore[type-arg]
    """Serialize cache analysis/cleanup to JSON-compatible dict."""
    data = _base("cache")
    data["mode"] = mode

    total_bytes = 0
    caches: list[dict] = []  # type: ignore[type-arg]
    for r in analyses:
        entry: dict = {  # type: ignore[type-arg]
            "module": r.module,
            "label": r.label,
            "available": r.available,
            "total_bytes": r.total_bytes,
            "total_human": format_size(r.total_bytes),
            "items": len(r.items),
        }
        if r.error:
            entry["error"] = r.error
        caches.append(entry)
        total_bytes += r.total_bytes

    data["caches"] = caches
    data["total_bytes"] = total_bytes
    data["total_human"] = format_size(total_bytes)

    if clean_results is not None:
        cleaned: list[dict] = []  # type: ignore[type-arg]
        for cr in clean_results:
            entry = {
                "module": cr.module,
                "label": cr.label,
                "freed_bytes": cr.freed_bytes,
                "freed_human": format_size(cr.freed_bytes),
                "items_removed": cr.items_removed,
            }
            if cr.errors:
                entry["errors"] = cr.errors
            cleaned.append(entry)
        data["cleaned"] = cleaned

    return data


def status_to_json(data: dict) -> dict:  # type: ignore[type-arg]
    """Wrap status data with standard envelope."""
    result = _base("status")
    result.update(data)
    return result


def doctor_to_json(diagnostics: list[Diagnostic]) -> dict:  # type: ignore[type-arg]
    """Serialize doctor diagnostics to JSON-compatible dict."""
    data = _base("doctor")
    data["diagnostics"] = [
        {
            "check": d.check,
            "status": d.status,
            "message": d.message,
            "details": list(d.details),
        }
        for d in diagnostics
    ]
    return data
