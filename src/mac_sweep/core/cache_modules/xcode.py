"""Xcode DerivedData cache module."""

from __future__ import annotations

import os

from mac_sweep.core.cache_modules.homebrew import _clean_filesystem
from mac_sweep.core.models import CacheAnalysis, CacheItem, CleanResult
from mac_sweep.core.size_utils import dir_size, file_age_days


class XcodeCache:
    """Analyze and clean Xcode DerivedData."""

    @property
    def name(self) -> str:
        return "xcode"

    @property
    def label(self) -> str:
        return "Xcode DerivedData"

    def analyze(self) -> CacheAnalysis:
        derived = os.path.expanduser(
            "~/Library/Developer/Xcode/DerivedData")

        if not os.path.isdir(derived):
            return CacheAnalysis(module=self.name, label=self.label)

        items: list[CacheItem] = []
        total = 0
        try:
            for entry in os.listdir(derived):
                full = os.path.join(derived, entry)
                if not os.path.isdir(full):
                    continue
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
