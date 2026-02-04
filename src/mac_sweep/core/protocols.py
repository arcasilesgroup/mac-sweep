"""Protocol definitions for mac-sweep plugin system."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from mac_sweep.core.models import CacheAnalysis, CleanResult


@runtime_checkable
class CacheModule(Protocol):
    """Protocol for cache scanning modules."""

    @property
    def name(self) -> str:
        """Module identifier (e.g. 'homebrew')."""
        ...

    @property
    def label(self) -> str:
        """Human-readable name (e.g. 'Homebrew Cache')."""
        ...

    def analyze(self) -> CacheAnalysis:
        """Analyze the cache and return analysis result."""
        ...

    def clean(
        self,
        analysis: CacheAnalysis,
        min_age_days: int = 7,
        execute: bool = False,
    ) -> CleanResult:
        """Clean cache items based on analysis."""
        ...
