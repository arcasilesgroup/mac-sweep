"""Tests for mac_sweep.core.cache_modules."""

import os
import tempfile

from mac_sweep.core.cache_modules import get_module, list_modules
from mac_sweep.core.cache_modules.docker import parse_docker_size
from mac_sweep.core.cache_modules.homebrew import _clean_filesystem
from mac_sweep.core.models import CacheAnalysis, CacheItem, CleanResult


class TestModuleRegistry:
    def test_module_list_not_empty(self):
        assert len(list_modules()) > 0

    def test_known_modules_present(self):
        for name in ("homebrew", "xcode", "docker", "npm",
                      "yarn", "pnpm", "pip"):
            assert name in list_modules()

    def test_get_unknown_module(self):
        assert get_module("nonexistent_xyz") is None

    def test_get_known_module(self):
        mod = get_module("homebrew")
        assert mod is not None
        assert mod.name == "homebrew"
        assert mod.label == "Homebrew Cache"

    def test_modules_have_analyze(self):
        for name in list_modules():
            mod = get_module(name)
            assert hasattr(mod, "analyze")
            assert hasattr(mod, "clean")


class TestParseDockerSize:
    def test_gigabytes(self):
        assert parse_docker_size("2.5GB") == int(2.5 * 1024**3)

    def test_megabytes(self):
        assert parse_docker_size("128MB") == int(128 * 1024**2)

    def test_kilobytes(self):
        assert parse_docker_size("512KB") == int(512 * 1024)

    def test_bytes(self):
        assert parse_docker_size("0B") == 0

    def test_with_percentage(self):
        result = parse_docker_size("2.5GB (50%)")
        assert result == int(2.5 * 1024**3)

    def test_empty_string(self):
        assert parse_docker_size("") == 0


class TestCleanFilesystem:
    def test_clean_unavailable_module(self):
        analysis = CacheAnalysis(module="test", label="Test",
                                 available=False)
        result = _clean_filesystem(analysis)
        assert result.freed_bytes == 0
        assert result.items_removed == 0

    def test_clean_empty_module(self):
        analysis = CacheAnalysis(module="test", label="Test",
                                 available=True, items=[])
        result = _clean_filesystem(analysis)
        assert result.freed_bytes == 0

    def test_clean_respects_age_guard(self):
        item = CacheItem(path="/tmp/test_young", size_bytes=1000,
                         age_days=1)
        analysis = CacheAnalysis(module="test", label="Test",
                                 available=True, items=[item],
                                 total_bytes=1000)
        result = _clean_filesystem(analysis, min_age_days=7, execute=False)
        assert result.freed_bytes == 0
        assert result.items_removed == 0

    def test_clean_protected_path_skipped(self):
        home = os.path.expanduser("~")
        item = CacheItem(path=home, size_bytes=999999, age_days=100)
        analysis = CacheAnalysis(module="test", label="Test",
                                 available=True, items=[item],
                                 total_bytes=999999)
        result = _clean_filesystem(analysis, min_age_days=0, execute=False)
        assert result.items_removed == 0
        assert len(result.errors) > 0
        assert "protected" in result.errors[0].lower()

    def test_clean_result_type(self):
        analysis = CacheAnalysis(module="test", label="Test",
                                 available=True, items=[])
        result = _clean_filesystem(analysis)
        assert isinstance(result, CleanResult)
        assert result.module == "test"
        assert result.label == "Test"
