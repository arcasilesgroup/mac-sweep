"""Tests for mac_sweep.core.safety."""

import os

import pytest

from mac_sweep.core.errors import (
    DependencyError,
    ProtectedAppError,
    ProtectedPathError,
    RunningProcessError,
)
from mac_sweep.core.safety import (
    ALLOWED_CACHE_PARENTS,
    APPLE_SYSTEM_APPS,
    PROTECTED_PATHS,
    check_dependency,
    check_protected,
    check_protected_path,
    is_brew_dependency,
    is_infrastructure,
    is_protected,
    is_protected_path,
)


class TestIsProtected:
    def test_apple_system_apps_are_protected(self):
        assert is_protected("Safari", "GUI Application")
        assert is_protected("Finder", "GUI Application")
        assert is_protected("System Settings", "GUI Application")
        assert is_protected("Mail", "GUI Application")
        assert is_protected("Terminal", "GUI Application")
        assert is_protected("Disk Utility", "GUI Application")

    def test_macos_installers_are_protected(self):
        assert is_protected("macOS Sequoia", "GUI Application")
        assert is_protected("macOS Sonoma", "GUI Application")
        assert is_protected("macOS Ventura", "GUI Application")

    def test_third_party_apps_not_protected(self):
        assert not is_protected("Slack", "GUI Application")
        assert not is_protected("Warp", "GUI Application")
        assert not is_protected("Discord", "GUI Application")
        assert not is_protected("Visual Studio Code", "GUI Application")

    def test_brew_formulas_not_protected(self):
        assert not is_protected("hugo", "Homebrew Formula")
        assert not is_protected("git", "Homebrew Formula")

    def test_protected_list_is_comprehensive(self):
        critical_apps = [
            "Finder", "Safari", "Mail", "Messages", "Calendar",
            "Notes", "Photos", "Music", "FaceTime", "Maps",
            "System Settings", "Terminal", "Activity Monitor",
        ]
        for app in critical_apps:
            assert app in APPLE_SYSTEM_APPS, f"{app} missing"


class TestCheckProtected:
    def test_raises_for_protected(self):
        with pytest.raises(ProtectedAppError):
            check_protected("Safari")

    def test_no_raise_for_third_party(self):
        check_protected("Slack")  # should not raise

    def test_raises_for_macos_installer(self):
        with pytest.raises(ProtectedAppError):
            check_protected("macOS Sonoma")


class TestIsBrewDependency:
    def test_dependency_detected(self):
        assert is_brew_dependency(
            "dependency (required by: python@3.12, node)")

    def test_explicit_not_dependency(self):
        assert not is_brew_dependency("explicitly installed")

    def test_empty_detail(self):
        assert not is_brew_dependency("")
        assert not is_brew_dependency(None)


class TestCheckDependency:
    def test_raises_for_dependency(self):
        with pytest.raises(DependencyError):
            check_dependency("dependency (required by: python@3.12)")

    def test_no_raise_for_explicit(self):
        check_dependency("explicitly installed")


class TestIsInfrastructure:
    def test_infrastructure_detected(self):
        assert is_infrastructure("Infrastructure")
        assert is_infrastructure("  Infrastructure  ")
        assert is_infrastructure("infrastructure")

    def test_non_infrastructure(self):
        assert not is_infrastructure("Active")
        assert not is_infrastructure("Dormant")
        assert not is_infrastructure("Unknown")


class TestProtectedPaths:
    def test_home_is_protected(self):
        assert is_protected_path(os.path.expanduser("~"))

    def test_documents_is_protected(self):
        assert is_protected_path(os.path.expanduser("~/Documents"))

    def test_root_is_protected(self):
        assert is_protected_path("/")

    def test_applications_is_protected(self):
        assert is_protected_path("/Applications")

    def test_system_is_protected(self):
        assert is_protected_path("/System")

    def test_random_path_is_protected(self):
        assert is_protected_path("/some/random/path")

    def test_npm_cache_is_allowed(self):
        cache_path = os.path.expanduser("~/.npm/_cacache/some_entry")
        assert not is_protected_path(cache_path)

    def test_pip_cache_is_allowed(self):
        cache_path = os.path.expanduser("~/Library/Caches/pip/some_pkg")
        assert not is_protected_path(cache_path)

    def test_xcode_derived_is_allowed(self):
        dd = os.path.expanduser(
            "~/Library/Developer/Xcode/DerivedData/MyProject-abc123")
        assert not is_protected_path(dd)

    def test_yarn_cache_is_allowed(self):
        cache_path = os.path.expanduser("~/Library/Caches/Yarn/v6")
        assert not is_protected_path(cache_path)

    def test_library_root_is_protected(self):
        assert is_protected_path(os.path.expanduser("~/Library"))

    def test_protected_paths_set_not_empty(self):
        assert len(PROTECTED_PATHS) > 0

    def test_allowed_parents_set_not_empty(self):
        assert len(ALLOWED_CACHE_PARENTS) > 0


class TestCheckProtectedPath:
    def test_raises_for_home(self):
        with pytest.raises(ProtectedPathError):
            check_protected_path(os.path.expanduser("~"))

    def test_no_raise_for_npm_cache(self):
        check_protected_path(
            os.path.expanduser("~/.npm/_cacache/entry"))
