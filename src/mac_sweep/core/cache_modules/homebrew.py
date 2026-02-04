"""Homebrew cache module."""

from __future__ import annotations

import os
import subprocess

from mac_sweep.core.models import CacheAnalysis, CacheItem, CleanResult
from mac_sweep.core.safety import is_protected_path
from mac_sweep.core.size_utils import dir_size, file_age_days


class HomebrewCache:
    """Analyze and clean Homebrew download cache."""

    @property
    def name(self) -> str:
        return "homebrew"

    @property
    def label(self) -> str:
        return "Homebrew Cache"

    def analyze(self) -> CacheAnalysis:
        try:
            result = subprocess.run(
                ["brew", "--cache"],
                capture_output=True, text=True, timeout=10,
            )
            cache_dir = result.stdout.strip()
        except Exception:
            return CacheAnalysis(module=self.name, label=self.label)

        if not cache_dir or not os.path.isdir(cache_dir):
            return CacheAnalysis(module=self.name, label=self.label)

        items: list[CacheItem] = []
        total = 0
        try:
            for entry in os.listdir(cache_dir):
                full = os.path.join(cache_dir, entry)
                sz = dir_size(full)
                age = file_age_days(full)
                items.append(CacheItem(
                    path=full, size_bytes=sz, age_days=max(age, 0),
                ))
                total += sz
        except OSError as e:
            return CacheAnalysis(
                module=self.name, label=self.label, error=str(e),
            )

        return CacheAnalysis(
            module=self.name, label=self.label, available=True,
            total_bytes=total, items=items,
        )

    def clean(
        self,
        analysis: CacheAnalysis,
        min_age_days: int = 7,
        execute: bool = False,
    ) -> CleanResult:
        return _clean_filesystem(
            analysis, min_age_days=min_age_days, execute=execute,
        )


def _clean_filesystem(
    analysis: CacheAnalysis,
    min_age_days: int = 7,
    execute: bool = False,
) -> CleanResult:
    """Generic filesystem cache cleaner."""
    import shutil

    result = CleanResult(module=analysis.module, label=analysis.label)

    if not analysis.available or not analysis.items:
        return result

    for item in analysis.items:
        if item.age_days < min_age_days:
            continue

        if is_protected_path(item.path):
            result.errors.append(f"Skipped protected path: {item.path}")
            continue

        result.freed_bytes += item.size_bytes
        result.items_removed += 1

        if execute:
            try:
                if os.path.isdir(item.path):
                    shutil.rmtree(item.path)
                elif os.path.isfile(item.path):
                    os.remove(item.path)
            except OSError as e:
                result.errors.append(f"Failed to remove {item.path}: {e}")
                result.freed_bytes -= item.size_bytes
                result.items_removed -= 1

    return result
