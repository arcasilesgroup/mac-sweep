"""Type system for mac-sweep.

All enums and frozen dataclasses used across the application.
Frozen dataclasses are immutable and hashable.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field


class Status(enum.Enum):
    """Application usage status."""

    ACTIVE = "Active"
    OCCASIONAL = "Occasional"
    DORMANT = "Dormant"
    UNKNOWN = "Unknown"
    INFRASTRUCTURE = "Infrastructure"


class Category(enum.Enum):
    """Software category."""

    GUI_APPLICATION = "GUI Application"
    HOMEBREW_FORMULA = "Homebrew Formula"
    NPM_GLOBAL = "npm Global"
    PIPX = "pipx"
    PIP = "pip"
    RUBY_GEM = "Ruby Gem"


class Source(enum.Enum):
    """Installation source."""

    HOMEBREW_CASK = "Homebrew Cask"
    APP_STORE = "App Store"
    APPLE = "Apple"
    MANUAL_INSTALL = "Manual Install"
    NPM = "npm"
    PIPX = "pipx"
    PIP = "pip"
    GEM = "gem"
    UNKNOWN = "Unknown"


class RemovalMethod(enum.Enum):
    """How to remove a piece of software."""

    BREW_CASK = "brew_cask"
    BREW_FORMULA = "brew_formula"
    GUI_TRASH = "gui_trash"
    NPM = "npm"
    PIPX = "pipx"
    PIP = "pip"


# ── Audit data models ──


@dataclass(frozen=True)
class AuditedApp:
    """A GUI application found during audit."""

    name: str
    source: str
    detail: str
    status: Status
    last_used: str
    description: str = ""
    size_bytes: int = 0


@dataclass(frozen=True)
class AuditedFormula:
    """A Homebrew formula found during audit."""

    name: str
    install_type: str  # "explicit" or "dependency"
    required_by: str
    status: Status
    description: str = ""


@dataclass(frozen=True)
class AuditedPackage:
    """A package manager package found during audit."""

    name: str
    category: Category
    version: str
    status: Status
    last_used: str = "N/A"
    description: str = ""
    extra: str = ""  # type for gems, etc.


@dataclass(frozen=True)
class AuditResult:
    """Complete result of an audit run."""

    apps: tuple[AuditedApp, ...] = ()
    formulas: tuple[AuditedFormula, ...] = ()
    npm_packages: tuple[AuditedPackage, ...] = ()
    pipx_packages: tuple[AuditedPackage, ...] = ()
    pip_packages: tuple[AuditedPackage, ...] = ()
    gem_packages: tuple[AuditedPackage, ...] = ()
    hostname: str = ""


# ── Cleanup data models ──


@dataclass(frozen=True)
class CleanupCandidate:
    """An item eligible for removal, with removal method and commands."""

    name: str
    category: str
    description: str
    status: str
    removal_method: str
    removal_cmd: tuple[str, ...] = ()
    undo_cmd: tuple[str, ...] = ()
    display_cmd: str = ""

    def __post_init__(self) -> None:
        if not self.display_cmd and self.removal_cmd:
            object.__setattr__(self, "display_cmd", " ".join(self.removal_cmd))


# ── Cache data models ──


@dataclass(frozen=True)
class CacheItem:
    """A single cache entry (file or directory) that can be cleaned."""

    path: str
    size_bytes: int = 0
    age_days: float = 0.0


@dataclass
class CacheAnalysis:
    """Result of analyzing a single cache module."""

    module: str
    label: str
    available: bool = False
    total_bytes: int = 0
    items: list[CacheItem] = field(default_factory=list)
    error: str = ""


@dataclass
class CleanResult:
    """Result of cleaning caches."""

    module: str
    label: str
    freed_bytes: int = 0
    items_removed: int = 0
    errors: list[str] = field(default_factory=list)


# ── Doctor data models ──


@dataclass(frozen=True)
class Diagnostic:
    """Result of a single health check."""

    check: str
    status: str  # "ok", "warning", "error"
    message: str
    details: tuple[str, ...] = ()
