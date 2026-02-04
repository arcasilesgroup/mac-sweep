"""npm cache module."""

from __future__ import annotations

import os

from mac_sweep.core.cache_modules.homebrew import _clean_filesystem
from mac_sweep.core.models import CacheAnalysis, CacheItem, CleanResult
from mac_sweep.core.size_utils import dir_size, file_age_days


class NpmCache:
    """Analyze and clean npm cache."""

    @property
    def name(self) -> str:
        return "npm"

    @property
    def label(self) -> str:
        return "npm Cache"

    def analyze(self) -> CacheAnalysis:
        cache_dir = os.path.expanduser("~/.npm/_cacache")

        if not os.path.isdir(cache_dir):
            return CacheAnalysis(module=self.name, label=self.label)

        total = dir_size(cache_dir)
        age = file_age_days(cache_dir)
        items = [CacheItem(
            path=cache_dir, size_bytes=total, age_days=max(age, 0),
        )]

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
