"""Cache module registry for mac-sweep."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mac_sweep.core.protocols import CacheModule

from mac_sweep.core.cache_modules.docker import DockerCache
from mac_sweep.core.cache_modules.homebrew import HomebrewCache
from mac_sweep.core.cache_modules.npm import NpmCache
from mac_sweep.core.cache_modules.pip_cache import PipCache
from mac_sweep.core.cache_modules.pnpm import PnpmCache
from mac_sweep.core.cache_modules.xcode import XcodeCache
from mac_sweep.core.cache_modules.yarn import YarnCache

_REGISTRY: dict[str, CacheModule] = {
    "homebrew": HomebrewCache(),
    "xcode": XcodeCache(),
    "docker": DockerCache(),
    "npm": NpmCache(),
    "yarn": YarnCache(),
    "pnpm": PnpmCache(),
    "pip": PipCache(),
}


def list_modules() -> list[str]:
    """Return list of available module names."""
    return list(_REGISTRY.keys())


def get_module(name: str) -> CacheModule | None:
    """Get a cache module by name."""
    return _REGISTRY.get(name)


def register(name: str, module: CacheModule) -> None:
    """Register a custom cache module."""
    _REGISTRY[name] = module
