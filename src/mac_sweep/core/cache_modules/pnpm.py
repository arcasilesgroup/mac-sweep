"""pnpm store cache module."""

from __future__ import annotations

import os

from mac_sweep.core.cache_modules.homebrew import _clean_filesystem
from mac_sweep.core.models import CacheAnalysis, CacheItem, CleanResult
from mac_sweep.core.size_utils import dir_size, file_age_days


class PnpmCache:
    """Analyze and clean pnpm store."""

    @property
    def name(self) -> str:
        return "pnpm"

    @property
    def label(self) -> str:
        return "pnpm Store"

    def analyze(self) -> CacheAnalysis:
        store_dir = os.path.expanduser("~/Library/pnpm/store")

        if not os.path.isdir(store_dir):
            return CacheAnalysis(module=self.name, label=self.label)

        total = dir_size(store_dir)
        age = file_age_days(store_dir)
        items = [CacheItem(
            path=store_dir, size_bytes=total, age_days=max(age, 0),
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
