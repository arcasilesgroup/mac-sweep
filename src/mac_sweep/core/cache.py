"""Cache orchestration for mac-sweep.

Pure logic — no I/O, no side effects. Returns data structures.
"""

from __future__ import annotations

from mac_sweep.core.cache_modules import get_module, list_modules
from mac_sweep.core.config import DEFAULT_MIN_CACHE_AGE_DAYS
from mac_sweep.core.models import CacheAnalysis, CleanResult


def analyze_all(
    modules: list[str] | None = None,
) -> list[CacheAnalysis]:
    """Analyze caches for the specified (or all) modules."""
    module_names = modules or list_modules()
    results: list[CacheAnalysis] = []

    for name in module_names:
        mod = get_module(name)
        if mod is None:
            results.append(CacheAnalysis(
                module=name, label=name,
                error=f"Unknown module: {name}",
            ))
        else:
            results.append(mod.analyze())

    return results


def clean_all(
    analyses: list[CacheAnalysis],
    min_age_days: int = DEFAULT_MIN_CACHE_AGE_DAYS,
    execute: bool = False,
) -> list[CleanResult]:
    """Clean cache items based on analyses."""
    results: list[CleanResult] = []

    for analysis in analyses:
        if not analysis.available:
            continue
        mod = get_module(analysis.module)
        if mod is None:
            continue
        cr = mod.clean(analysis, min_age_days=min_age_days, execute=execute)
        results.append(cr)

    return results
