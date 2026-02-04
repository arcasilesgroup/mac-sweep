"""Tests for mac_sweep.core.config."""

import os
import tempfile

from mac_sweep.core.config import (
    DEFAULT_ACTIVE_DAYS,
    DEFAULT_MIN_CACHE_AGE_DAYS,
    DEFAULT_OCCASIONAL_DAYS,
    SweepConfig,
    _read_config_file,
)


class TestSweepConfig:
    def test_defaults(self):
        cfg = SweepConfig()
        assert cfg.active_days == DEFAULT_ACTIVE_DAYS
        assert cfg.occasional_days == DEFAULT_OCCASIONAL_DAYS
        assert cfg.min_cache_age_days == DEFAULT_MIN_CACHE_AGE_DAYS
        assert cfg.anthropic_api_key == ""
        assert cfg.openai_api_key == ""

    def test_custom_values(self):
        cfg = SweepConfig(active_days=14, occasional_days=60)
        assert cfg.active_days == 14
        assert cfg.occasional_days == 60


class TestReadConfigFile:
    def test_nonexistent_file(self):
        result = _read_config_file("/nonexistent/path/12345")
        assert result == {}

    def test_valid_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg",
                                         delete=False) as f:
            f.write("ANTHROPIC_API_KEY=sk-test-123\n")
            f.write("OPENAI_API_KEY=sk-openai-456\n")
            f.write("# comment line\n")
            f.write("active_days=14\n")
            path = f.name
        try:
            result = _read_config_file(path)
            assert result["ANTHROPIC_API_KEY"] == "sk-test-123"
            assert result["OPENAI_API_KEY"] == "sk-openai-456"
            assert result["active_days"] == "14"
        finally:
            os.unlink(path)

    def test_comments_ignored(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg",
                                         delete=False) as f:
            f.write("# This is a comment\n")
            f.write("KEY=value\n")
            path = f.name
        try:
            result = _read_config_file(path)
            assert "KEY" in result
            assert len(result) == 1
        finally:
            os.unlink(path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".cfg",
                                         delete=False) as f:
            path = f.name
        try:
            result = _read_config_file(path)
            assert result == {}
        finally:
            os.unlink(path)
