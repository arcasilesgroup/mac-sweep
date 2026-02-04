"""Audit engine for mac-sweep.

Processes raw data collected by collect-data.sh (Phase 0) and produces
an AuditResult. This is a pure core module — no I/O, no side effects.
It returns data only.

Usage:
    result = process_audit(tmpdir, brew_prefix)
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime

from mac_sweep.core.config import DEFAULT_ACTIVE_DAYS, DEFAULT_OCCASIONAL_DAYS
from mac_sweep.core.descriptions import KNOWN_APP_DESCRIPTIONS, get_app_description
from mac_sweep.core.models import (
    AuditedApp,
    AuditedFormula,
    AuditedPackage,
    AuditResult,
    Category,
    Status,
)

# ── Constants ──

_SEVEN_DAYS = DEFAULT_ACTIVE_DAYS * 86400
_THIRTY_DAYS = DEFAULT_OCCASIONAL_DAYS * 86400


# ── Helper functions ──


def classify_age(epoch: float | None, now: float | None = None) -> Status:
    """Classify based on age from now."""
    if now is None:
        now = time.time()
    if not epoch or epoch <= 0:
        return Status.UNKNOWN
    age = now - epoch
    if age <= _SEVEN_DAYS:
        return Status.ACTIVE
    elif age <= _THIRTY_DAYS:
        return Status.OCCASIONAL
    else:
        return Status.DORMANT


def format_date(epoch: float | None) -> str:
    """Format epoch timestamp as YYYY-MM-DD string."""
    if not epoch or epoch <= 0:
        return "N/A"
    try:
        return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d")
    except Exception:
        return "N/A"


def parse_mdls_date(raw: str | None) -> float:
    """Parse kMDItemLastUsedDate string to epoch."""
    if not raw or raw in ("(null)", "null", ""):
        return 0
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S +0000"):
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            return dt.timestamp()
        except Exception:
            continue
    return 0


def _read_lines(tmpdir: str, filename: str) -> list[str]:
    """Read non-empty lines from a file in tmpdir."""
    path = os.path.join(tmpdir, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.rstrip("\n") for line in f if line.strip()]


def _read_file(tmpdir: str, filename: str) -> str:
    """Read entire file content from tmpdir."""
    path = os.path.join(tmpdir, filename)
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()


def _load_json(tmpdir: str, filename: str) -> dict | list:
    """Load JSON from tmpdir, returning empty dict on error."""
    path = os.path.join(tmpdir, filename)
    if not os.path.exists(path):
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


# ── Main processing ──


def process_audit(
    tmpdir: str,
    brew_prefix: str = "",
    now: float | None = None,
) -> AuditResult:
    """Process collected data and return AuditResult.

    This function NEVER prints, NEVER writes files.
    """
    if now is None:
        now = time.time()

    # ── Description sources ──
    pip_descriptions = _load_json(tmpdir, "pip_descriptions.json")
    if not isinstance(pip_descriptions, dict):
        pip_descriptions = {}

    # ── Phase 1: Cask mapping ──
    brew_data = _load_json(tmpdir, "brew_info.json")
    if not isinstance(brew_data, dict):
        brew_data = {}
    cask_map: dict[str, tuple[str, str, str]] = {}
    cask_descriptions: dict[str, str] = {}
    formula_descriptions: dict[str, str] = {}

    for f_info in brew_data.get("formulae", []):
        fname = f_info.get("name", "")
        fdesc = f_info.get("desc", "") or ""
        if fname and fdesc:
            formula_descriptions[fname] = fdesc

    for c in brew_data.get("casks", []):
        token = c.get("token", "")
        name = (c.get("name") or [""])[0] or token
        desc = c.get("desc", "") or ""
        installed = c.get("installed") or ""
        if isinstance(installed, dict):
            installed = installed.get("version", "")
        version = str(installed)
        if desc:
            cask_descriptions[token] = desc
        for art in c.get("artifacts", []):
            if isinstance(art, dict) and "app" in art:
                for a in art["app"]:
                    basename = os.path.basename(a)
                    cask_map[basename] = (token, name, version)

    # ── Phase 2: Scan /Applications ──

    appstore_apps: set[str] = set()
    for line in _read_lines(tmpdir, "appstore_apps.txt"):
        appstore_apps.add(os.path.basename(line))

    sysprof_data = _load_json(tmpdir, "sysprof.json")
    if not isinstance(sysprof_data, dict):
        sysprof_data = {}
    sysprof_map: dict[str, str] = {}
    for item in sysprof_data.get("SPApplicationsDataType", []):
        loc = item.get("path", "")
        obtained = item.get("obtained_from", "")
        if loc:
            sysprof_map[os.path.basename(loc)] = obtained

    running_apps: set[str] = set()
    ps_text = _read_file(tmpdir, "ps_aux.txt")
    for m in re.finditer(r'/Applications/([^/]+\.app)/', ps_text):
        running_apps.add(m.group(1))

    launch_agents_content = _read_file(
        tmpdir, "launch_agents_content.txt"
    ).lower()

    mdls_map: dict[str, tuple[float, str, str]] = {}
    for line in _read_lines(tmpdir, "mdls_results.txt"):
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        apath, last_raw, bundle = parts[0], parts[1], parts[2]
        kind = parts[3] if len(parts) > 3 else "(null)"
        base = os.path.basename(apath)
        epoch = parse_mdls_date(last_raw)
        mdls_map[base] = (epoch, bundle, kind)

    def determine_source(app_base: str) -> tuple[str, str]:
        if app_base in cask_map:
            token = cask_map[app_base][0]
            return ("Homebrew Cask", f"cask: {token}")
        if app_base in appstore_apps:
            return ("App Store", "App Store")
        obtained = sysprof_map.get(app_base, "")
        if obtained == "apple":
            return ("Apple", "Apple")
        if obtained == "identified_developer":
            return ("Manual Install", "Manual Install")
        if obtained == "mac_app_store":
            return ("App Store", "App Store")
        return ("Unknown", "Unknown")

    def determine_usage(app_base: str) -> tuple[Status, str]:
        if app_base in running_apps:
            epoch = mdls_map.get(app_base, (0, "", ""))[0]
            return (Status.ACTIVE, format_date(epoch))

        mdls_entry = mdls_map.get(app_base, (0, "(null)", "(null)"))
        epoch, bundle_id = mdls_entry[0], mdls_entry[1]

        if epoch > 0:
            return (classify_age(epoch, now), format_date(epoch))

        if bundle_id and bundle_id != "(null)":
            if bundle_id.lower() in launch_agents_content:
                return (Status.ACTIVE, "N/A")

        if bundle_id and bundle_id != "(null)":
            cache_dir = os.path.expanduser(
                f"~/Library/Caches/{bundle_id}")
            if os.path.isdir(cache_dir):
                try:
                    mtime = os.stat(cache_dir).st_mtime
                    status = classify_age(mtime, now)
                    if status in (Status.ACTIVE, Status.OCCASIONAL):
                        return (status, format_date(mtime))
                except Exception:
                    pass

        return (Status.UNKNOWN, "N/A")

    # App sizes
    app_sizes: dict[str, int] = {}
    for line in _read_lines(tmpdir, "app_sizes.txt"):
        parts = line.split("\t")
        if len(parts) >= 2:
            try:
                app_sizes[parts[0]] = int(parts[1]) * 1024
            except ValueError:
                pass

    apps_classified: list[AuditedApp] = []
    cask_tokens_seen: set[str] = set()

    for line in _read_lines(tmpdir, "app_paths.txt"):
        app_base = os.path.basename(line)
        app_name = app_base.rsplit(".app", 1)[0]

        source_type, source_detail = determine_source(app_base)
        status, last_used = determine_usage(app_base)
        description = get_app_description(
            app_name, app_base,
            cask_map=cask_map,
            cask_descriptions=cask_descriptions,
            mdls_map=mdls_map,
        )

        if source_type == "Homebrew Cask" and app_base in cask_map:
            cask_tokens_seen.add(cask_map[app_base][0])

        size_bytes = app_sizes.get(line, 0)

        apps_classified.append(AuditedApp(
            name=app_name,
            source=source_type,
            detail=source_detail,
            status=status,
            last_used=last_used,
            description=description,
            size_bytes=size_bytes,
        ))

    # ── Phase 3: Homebrew formulas ──

    brew_leaves = set(_read_lines(tmpdir, "brew_leaves.txt"))
    brew_formulas = _read_lines(tmpdir, "brew_formulas.txt")

    brew_required_by: dict[str, list[str]] = {}
    for f_info in brew_data.get("formulae", []):
        pkg = f_info.get("name", "")
        for dep in f_info.get("dependencies", []):
            brew_required_by.setdefault(dep, []).append(pkg)

    for line in _read_lines(tmpdir, "brew_deps.txt"):
        if ":" not in line:
            continue
        pkg, deps_str = line.split(":", 1)
        pkg = pkg.strip()
        for dep in deps_str.split():
            dep = dep.strip()
            if dep:
                brew_required_by.setdefault(dep, []).append(pkg)

    for dep in brew_required_by:
        brew_required_by[dep] = sorted(set(brew_required_by[dep]))

    formulas_classified: list[AuditedFormula] = []
    for formula in brew_formulas:
        if not formula:
            continue
        is_explicit = formula in brew_leaves
        rdeps = brew_required_by.get(formula, [])
        if not rdeps:
            for key in brew_required_by:
                base_key = key.split("@")[0]
                base_formula = formula.split("@")[0]
                if base_key == base_formula and key != formula:
                    rdeps = brew_required_by[key]
                    break
        required_by = (", ".join(sorted(set(rdeps)))
                       if not is_explicit else "")
        if not is_explicit and not required_by:
            required_by = "unknown"

        status = Status.UNKNOWN
        if brew_prefix:
            bin_path = os.path.join(brew_prefix, "bin", formula)
            if os.path.exists(bin_path):
                try:
                    atime = os.stat(bin_path).st_atime
                    status = classify_age(atime, now)
                except Exception:
                    pass

        desc = formula_descriptions.get(formula, "")
        formulas_classified.append(AuditedFormula(
            name=formula,
            install_type="explicit" if is_explicit else "dependency",
            required_by=required_by,
            status=status,
            description=desc,
        ))

    # ── Phase 4: npm global ──

    npm_data = _load_json(tmpdir, "npm_global.json")
    if not isinstance(npm_data, dict):
        npm_data = {}
    npm_prefix = _read_file(tmpdir, "npm_prefix.txt").strip()
    npm_packages: list[AuditedPackage] = []

    for pkg_name, info in sorted(npm_data.get("dependencies", {}).items()):
        version = info.get("version", "?") if isinstance(info, dict) else "?"
        status = Status.UNKNOWN
        last_used = "N/A"
        if npm_prefix:
            bin_path = os.path.join(npm_prefix, "bin", pkg_name)
            if os.path.exists(bin_path):
                try:
                    atime = os.stat(bin_path).st_atime
                    status = classify_age(atime, now)
                    last_used = format_date(atime)
                except Exception:
                    pass
        npm_desc = ""
        if npm_prefix:
            pkg_json_path = os.path.join(
                npm_prefix, "lib", "node_modules", pkg_name, "package.json")
            if os.path.exists(pkg_json_path):
                try:
                    with open(pkg_json_path) as pf:
                        pdata = json.load(pf)
                        npm_desc = pdata.get("description", "") or ""
                except Exception:
                    pass
        npm_packages.append(AuditedPackage(
            name=pkg_name,
            category=Category.NPM_GLOBAL,
            version=version,
            status=status,
            last_used=last_used,
            description=npm_desc,
        ))

    # ── Phase 5: pipx ──

    pipx_packages: list[AuditedPackage] = []
    for line in _read_lines(tmpdir, "pipx_list.txt"):
        parts = line.split(None, 1)
        if not parts:
            continue
        pkg_name = parts[0]
        version = parts[1] if len(parts) > 1 else ""
        status = Status.UNKNOWN
        last_used = "N/A"
        bin_path = os.path.expanduser(f"~/.local/bin/{pkg_name}")
        if os.path.exists(bin_path):
            try:
                atime = os.stat(bin_path).st_atime
                status = classify_age(atime, now)
                last_used = format_date(atime)
            except Exception:
                pass
        pipx_desc = pip_descriptions.get(pkg_name.lower(), "")
        pipx_packages.append(AuditedPackage(
            name=pkg_name,
            category=Category.PIPX,
            version=version,
            status=status,
            last_used=last_used,
            description=pipx_desc,
        ))

    # ── Phase 6: pip ──

    pip_path = os.path.join(tmpdir, "pip_list.json")
    pip_data = _load_json(tmpdir, "pip_list.json") if os.path.exists(pip_path) else []
    if not isinstance(pip_data, list):
        pip_data = []
    pip_packages: list[AuditedPackage] = []
    for pkg in sorted(pip_data, key=lambda x: x.get("name", "").lower()):
        pname = pkg.get("name", "")
        pip_desc = pip_descriptions.get(pname.lower(), "")
        pip_packages.append(AuditedPackage(
            name=pname,
            category=Category.PIP,
            version=pkg.get("version", ""),
            status=Status.INFRASTRUCTURE,
            last_used="N/A",
            description=pip_desc,
        ))

    # ── Phase 7: Ruby gems ──

    gem_packages: list[AuditedPackage] = []
    user_gemdir = _read_file(tmpdir, "gem_userdir.txt").strip()
    for line in _read_lines(tmpdir, "gem_list.txt"):
        m = re.match(r'^(\S+)\s+\((.+)\)$', line)
        if not m:
            continue
        gem_name = m.group(1)
        gem_versions = m.group(2)
        gem_type = "system-default"
        if user_gemdir:
            user_gems_path = os.path.join(user_gemdir, "gems")
            if os.path.isdir(user_gems_path):
                for d in os.listdir(user_gems_path):
                    if d.startswith(gem_name + "-"):
                        gem_type = "user-installed"
                        break
        gem_packages.append(AuditedPackage(
            name=gem_name,
            category=Category.RUBY_GEM,
            version=gem_versions,
            status=Status.INFRASTRUCTURE,
            last_used="N/A",
            description="System Ruby gem",
            extra=gem_type,
        ))

    hostname = ""
    try:
        hostname = os.uname().nodename
    except Exception:
        pass

    return AuditResult(
        apps=tuple(apps_classified),
        formulas=tuple(formulas_classified),
        npm_packages=tuple(npm_packages),
        pipx_packages=tuple(pipx_packages),
        pip_packages=tuple(pip_packages),
        gem_packages=tuple(gem_packages),
        hostname=hostname,
    )
