"""Report formatting for mac-sweep.

Generates Markdown, CSV, and terminal output from core data structures.
"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime

from mac_sweep.core.models import (
    AuditResult,
    CacheAnalysis,
    CleanResult,
    Diagnostic,
    Status,
)
from mac_sweep.core.size_utils import format_size

STATUS_EMOJI: dict[str, str] = {
    "Active": "\U0001f7e2",       # green circle
    "Occasional": "\U0001f7e1",   # yellow circle
    "Dormant": "\U0001f534",      # red circle
    "Unknown": "\u26aa",          # white circle
    "Infrastructure": "\u2699\ufe0f",  # gear
}

DIAGNOSTIC_EMOJI: dict[str, str] = {
    "ok": "\u2713",       # check mark
    "warning": "\u26a0",  # warning
    "error": "\u2717",    # cross
}


def format_status(status: Status | str) -> str:
    """Format status with emoji."""
    name = status.value if isinstance(status, Status) else status
    return f"{STATUS_EMOJI.get(name, '')} {name}"


def _md_status(s: str) -> str:
    """Format status with emoji for Markdown."""
    return f"{STATUS_EMOJI.get(s, '')} {s}"


def _esc_pipe(s: str) -> str:
    """Escape pipe characters for Markdown table cells."""
    return str(s).replace("|", "\\|")


def generate_csv_report(result: AuditResult) -> str:
    """Generate CSV audit report as a string."""
    output = io.StringIO()
    w = csv.writer(output)
    w.writerow(["Category", "Name", "Source", "Detail", "Status",
                 "Last Used", "Description", "Size"])

    for app in result.apps:
        w.writerow(["GUI Application", app.name, app.source,
                     app.detail, app.status.value, app.last_used,
                     app.description, app.size_bytes])

    for f in result.formulas:
        detail = ("explicitly installed" if f.install_type == "explicit"
                  else f"dependency (required by: {f.required_by})")
        w.writerow(["Homebrew Formula", f.name, f.install_type,
                     detail, f.status.value, "N/A",
                     f.description, ""])

    for p in result.npm_packages:
        w.writerow(["npm Global", p.name, "npm", f"v{p.version}",
                     p.status.value, p.last_used,
                     p.description, ""])

    for p in result.pipx_packages:
        w.writerow(["pipx", p.name, "pipx", p.version,
                     p.status.value, p.last_used,
                     p.description, ""])

    for p in result.pip_packages:
        w.writerow(["pip", p.name, "pip", f"v{p.version}",
                     p.status.value, p.last_used,
                     p.description, ""])

    for g in result.gem_packages:
        w.writerow(["Ruby Gem", g.name, "gem",
                     f"{g.extra} ({g.version})",
                     "Infrastructure", "N/A",
                     g.description, ""])

    return output.getvalue()


def generate_markdown_report(result: AuditResult) -> str:
    """Generate Markdown audit report as a string."""
    counts: dict[str, int] = {
        "Active": 0, "Occasional": 0, "Dormant": 0,
        "Unknown": 0, "Infrastructure": 0,
    }
    cleanup: list[tuple[str, str, str, str]] = []
    lines: list[str] = []

    lines.append("# macOS Application Audit Report")
    lines.append("")
    lines.append(f"> **Generated:** "
                 f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    hostname = result.hostname or os.uname().nodename
    lines.append(f"> **Host:** {hostname}")
    lines.append("")
    lines.append("**Status Legend:** "
                 + " ".join(f"{STATUS_EMOJI[s]} {s}"
                            for s in ("Active", "Occasional", "Dormant",
                                      "Unknown", "Infrastructure")))
    lines.append("")

    # ── GUI Applications ──
    lines.append("## GUI Applications (/Applications)")
    lines.append("")

    for sg in ["Homebrew Cask", "App Store", "Apple",
               "Manual Install", "Unknown"]:
        entries = [a for a in result.apps if a.source == sg]
        if not entries:
            continue
        lines.append(f"### {sg} ({len(entries)} apps)")
        lines.append("")
        lines.append("| Name | Description | Source Detail "
                     "| Size | Status | Last Used |")
        lines.append("|:-----|:------------|:-------------|"
                     ":-----|:-------|:----------|")
        for e in entries:
            desc = _esc_pipe(e.description)
            size_str = format_size(e.size_bytes) if e.size_bytes else "-"
            status_val = e.status.value
            lines.append(
                f"| {_esc_pipe(e.name)} | {desc} "
                f"| {_esc_pipe(e.detail)} "
                f"| {size_str} "
                f"| {_md_status(status_val)} | {e.last_used} |"
            )
            if status_val in counts:
                counts[status_val] += 1
            if status_val == "Dormant":
                cleanup.append(("GUI Application", e.name,
                                sg, e.description))
        lines.append("")

    # ── Homebrew Formulas ──
    lines.append("## Homebrew Formulas")
    lines.append("")

    explicit = [f for f in result.formulas if f.install_type == "explicit"]
    deps = [f for f in result.formulas if f.install_type == "dependency"]

    if result.formulas:
        lines.append(f"### Explicitly Installed ({len(explicit)} formulas)")
        lines.append("")
        lines.append("| Name | Description | Status |")
        lines.append("|:-----|:------------|:-------|")
        for e in explicit:
            desc = _esc_pipe(e.description)
            status_val = e.status.value
            lines.append(
                f"| {_esc_pipe(e.name)} | {desc} "
                f"| {_md_status(status_val)} |"
            )
            if status_val in counts:
                counts[status_val] += 1
            if status_val == "Dormant":
                cleanup.append(("Homebrew Formula", e.name,
                                "brew", e.description))
        lines.append("")

        lines.append(
            f"### Auto-Installed Dependencies ({len(deps)} formulas)")
        lines.append("")
        lines.append("| Name | Description | Required By | Status |")
        lines.append("|:-----|:------------|:------------|:-------|")
        for e in deps:
            req = e.required_by
            if len(req) > 40:
                req = req[:37] + "..."
            desc = _esc_pipe(e.description)
            status_val = e.status.value
            lines.append(
                f"| {_esc_pipe(e.name)} | {desc} "
                f"| {_esc_pipe(req)} | {_md_status(status_val)} |"
            )
            if status_val in counts:
                counts[status_val] += 1
        lines.append("")
    else:
        lines.append("*(Homebrew not available)*")
        lines.append("")

    # ── Package Managers ──
    lines.append("## Package Managers")
    lines.append("")

    # npm
    lines.append("### npm Global Packages")
    lines.append("")
    if result.npm_packages:
        lines.append("| Name | Description | Version | Status | Last Used |")
        lines.append("|:-----|:------------|:--------|:-------|:----------|")
        for p in result.npm_packages:
            desc = _esc_pipe(p.description)
            status_val = p.status.value
            lines.append(
                f"| {_esc_pipe(p.name)} | {desc} | {p.version} "
                f"| {_md_status(status_val)} | {p.last_used} |"
            )
            if status_val in counts:
                counts[status_val] += 1
            if status_val == "Dormant":
                cleanup.append(("npm Global", p.name,
                                "npm", p.description))
    else:
        lines.append("*(no npm global packages or npm not available)*")
    lines.append("")

    # pipx
    lines.append("### pipx Packages")
    lines.append("")
    if result.pipx_packages:
        lines.append("| Name | Description | Version | Status | Last Used |")
        lines.append("|:-----|:------------|:--------|:-------|:----------|")
        for p in result.pipx_packages:
            desc = _esc_pipe(p.description)
            status_val = p.status.value
            lines.append(
                f"| {_esc_pipe(p.name)} | {desc} | {p.version} "
                f"| {_md_status(status_val)} | {p.last_used} |"
            )
            if status_val in counts:
                counts[status_val] += 1
            if status_val == "Dormant":
                cleanup.append(("pipx", p.name,
                                "pipx", p.description))
    else:
        lines.append("*(no pipx packages or pipx not available)*")
    lines.append("")

    # pip
    lines.append("### pip Packages")
    lines.append("")
    if result.pip_packages:
        lines.append(
            f"*{len(result.pip_packages)} packages -- "
            f"classified as Infrastructure*")
        lines.append("")
        lines.append("| Name | Description | Version | Status |")
        lines.append("|:-----|:------------|:--------|:-------|")
        for p in result.pip_packages:
            desc = _esc_pipe(p.description)
            lines.append(
                f"| {_esc_pipe(p.name)} | {desc} | {p.version} "
                f"| {_md_status('Infrastructure')} |"
            )
            counts["Infrastructure"] += 1
    else:
        lines.append("*(no pip packages or pip3 not available)*")
    lines.append("")

    # gems
    lines.append("### Ruby Gems")
    lines.append("")
    if result.gem_packages:
        lines.append(f"*{len(result.gem_packages)} gems*")
        lines.append("")
        lines.append("| Name | Description | Version(s) | Type |")
        lines.append("|:-----|:------------|:-----------|:-----|")
        for g in result.gem_packages:
            ver = g.version
            if len(ver) > 30:
                ver = ver[:27] + "..."
            desc = _esc_pipe(g.description)
            lines.append(
                f"| {_esc_pipe(g.name)} | {desc} "
                f"| {_esc_pipe(ver)} | {g.extra} |"
            )
            counts["Infrastructure"] += 1
    else:
        lines.append("*(no gems or gem not available)*")
    lines.append("")

    # ── Summary ──
    lines.append("## Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|:-------|------:|")
    for s in ("Active", "Occasional", "Dormant", "Unknown", "Infrastructure"):
        lines.append(f"| {_md_status(s)} | {counts[s]} |")
    total = sum(counts.values())
    lines.append(f"| **Total** | **{total}** |")
    lines.append("")

    # ── Disk Usage Summary ──
    dormant_size = sum(a.size_bytes for a in result.apps
                       if a.status == Status.DORMANT)
    total_size = sum(a.size_bytes for a in result.apps)
    if total_size > 0:
        lines.append("## Disk Usage Summary")
        lines.append("")
        lines.append("| Metric | Size |")
        lines.append("|:-------|-----:|")
        lines.append(f"| Total GUI app size | {format_size(total_size)} |")
        lines.append(f"| Dormant app size | {format_size(dormant_size)} |")
        lines.append("")

    # ── Cleanup Guidance ──
    lines.append("## Cleanup Guidance")
    lines.append("")
    if cleanup:
        lines.append("The following dormant, non-dependency items are "
                     "candidates for removal:")
        lines.append("")
        lines.append("| Name | Category | Removal Command |")
        lines.append("|:-----|:---------|:----------------|")
        for cat, name, src, desc in cleanup:
            if cat == "GUI Application":
                cmd = "Use `./sweep cleanup --execute`"
            elif cat == "Homebrew Formula":
                cmd = f"`brew uninstall {name}`"
            elif cat == "npm Global":
                cmd = f"`npm uninstall -g {name}`"
            elif cat == "pipx":
                cmd = f"`pipx uninstall {name}`"
            else:
                cmd = ""
            lines.append(f"| {_esc_pipe(name)} | {cat} | {cmd} |")
        lines.append("")
        lines.append("> **Tip:** Run `./sweep cleanup` for a safe, "
                     "interactive cleanup experience.")
    else:
        lines.append("*(no cleanup candidates found)*")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated by "
                 "[mac-sweep](https://github.com/arcasilesgroup/mac-sweep)*")

    return "\n".join(lines) + "\n"


def generate_cache_report(
    analyses: list[CacheAnalysis],
    clean_results: list[CleanResult] | None = None,
) -> str:
    """Generate Markdown report for cache analysis."""
    lines: list[str] = []
    lines.append("# Developer Cache Report")
    lines.append("")
    lines.append(f"> **Generated:** "
                 f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append("")

    lines.append("## Cache Analysis")
    lines.append("")
    lines.append("| Module | Size | Items | Status |")
    lines.append("|:-------|-----:|------:|:-------|")

    total = 0
    for r in analyses:
        if r.error:
            status = f"error: {r.error}"
        elif not r.available:
            status = "not found"
        else:
            status = "available"
        size_str = format_size(r.total_bytes) if r.available else "-"
        item_count = str(len(r.items)) if r.available else "-"
        lines.append(
            f"| {_esc_pipe(r.label)} | {size_str} | {item_count} | {status} |")
        total += r.total_bytes

    lines.append(f"| **Total** | **{format_size(total)}** | | |")
    lines.append("")

    if clean_results:
        lines.append("## Cleanup Results")
        lines.append("")
        lines.append("| Module | Freed | Items |")
        lines.append("|:-------|------:|------:|")
        total_freed = 0
        total_items = 0
        for cr in clean_results:
            if cr.items_removed > 0:
                lines.append(
                    f"| {_esc_pipe(cr.label)} | "
                    f"{format_size(cr.freed_bytes)} | {cr.items_removed} |")
                total_freed += cr.freed_bytes
                total_items += cr.items_removed
        lines.append(
            f"| **Total** | **{format_size(total_freed)}** | "
            f"**{total_items}** |")
        lines.append("")

    lines.append("---")
    lines.append("*Report generated by "
                 "[mac-sweep](https://github.com/arcasilesgroup/mac-sweep)*")

    return "\n".join(lines) + "\n"


def format_doctor_output(diagnostics: list[Diagnostic]) -> str:
    """Format doctor diagnostics for terminal display."""
    lines: list[str] = []
    lines.append("mac-sweep doctor")
    lines.append("\u2550" * 35)

    for d in diagnostics:
        emoji = DIAGNOSTIC_EMOJI.get(d.status, "?")
        lines.append(f"  {emoji} {d.message}")
        for detail in d.details:
            lines.append(f"    - {detail}")

    lines.append("\u2550" * 35)
    return "\n".join(lines)


def format_status_output(data: dict) -> str:  # type: ignore[type-arg]
    """Format status summary for terminal display."""
    lines: list[str] = []
    lines.append("mac-sweep status")
    lines.append("\u2550" * 35)

    counts = data.get("counts", {})
    disk = data.get("disk", {})

    lines.append(f"  Apps installed:      {counts.get('gui_apps', '?')}")
    lines.append(f"  Homebrew formulas:   {counts.get('formulas', '?')}")
    lines.append(f"  Packages (npm/pip):  {counts.get('packages', '?')}")
    lines.append("")

    dormant = counts.get("dormant", 0)
    if dormant:
        dormant_bytes = disk.get("dormant_bytes", 0)
        lines.append(
            f"  Dormant apps:          {dormant}  "
            f"({format_size(dormant_bytes)} recoverable)"
        )

    cache_bytes = disk.get("cache_bytes", 0)
    if cache_bytes:
        lines.append(
            f"  Dev caches:                "
            f"({format_size(cache_bytes)} recoverable)"
        )

    lines.append("")

    audit_age = data.get("audit_age_hours")
    if audit_age is not None:
        lines.append(f"  Last audit:        {audit_age:.0f}h ago")
    else:
        lines.append("  Last audit:        never")

    lines.append("\u2550" * 35)
    return "\n".join(lines)
